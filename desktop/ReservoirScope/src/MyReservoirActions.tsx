import type { SustainedActionControls, SustainedActionDecision, SustainedActionReceipt, SustainedAuthoredRequest, SustainedJournal, SustainedReservoirInput, SustainedSummary } from './myReservoirTypes';

const parameterNames: Record<keyof SustainedActionControls, string> = { leak: 'Recurrent leak', recurrentGain: 'Recurrent gain', feedbackScale: 'Text feedback scale' };
const number = (value: number) => Number.isFinite(value) ? Number(value.toPrecision(6)).toString() : 'Unavailable';
export function actionDescription(request: SustainedAuthoredRequest | null): string {
  if (!request) return 'No valid action selected';
  switch (request.kind) {
    case 'none': return 'NONE · continue without an additional intervention';
    case 'pulse': return `PULSE · ${request.direction} · strength ${number(request.strength)}`;
    case 'tune': return `TUNE · ${parameterNames[request.parameter]} to ${number(request.value)}`;
    case 'release': return 'RELEASE · return controls to session settings';
  }
}
export function actionReceiptStatus(receipt: SustainedActionReceipt): string {
  return receipt.status === 'applied' ? `Action applied at step ${receipt.appliedStep}`
    : receipt.status === 'unchanged' ? `No additional intervention at step ${receipt.appliedStep}`
      : `Action rejected at step ${receipt.appliedStep}`;
}

function Controls({ controls }: { controls: SustainedActionControls }) {
  return <dl className="my-reservoir-data my-reservoir-action-controls">
    {Object.entries(parameterNames).map(([key, label]) => <div key={key}><dt>{label}</dt><dd>{number(controls[key as keyof SustainedActionControls])}</dd></div>)}
  </dl>;
}
function ReservoirInput({ input, appliedStep, skipped = false }: { input: SustainedReservoirInput; appliedStep?: number; skipped?: boolean }) {
  const applied = appliedStep !== undefined;
  const label = skipped ? `Text-input choice skipped · ${input.disposition}` : input.disposition === 'send'
    ? applied ? `Text input allowed at step ${appliedStep}` : 'Text input selected: send'
    : input.disposition === 'rejected'
      ? applied ? `Input directive rejected; text input withheld at step ${appliedStep}` : 'Input directive rejected; text input will be withheld'
      : applied ? `Text input withheld at step ${appliedStep}` : 'Text input selected: withhold';
  return <div className="my-reservoir-input-decision">
    <p><strong>{label}</strong></p>
    {input.rejection && <p className="my-reservoir-action-rejection">{input.rejection}</p>}
    {skipped ? <p>No text-input application was recorded. This entry’s automatic memory exposure was skipped.</p> : input.disposition !== 'send' && <p>{applied ? 'The previous held text input was replaced with zero. The journal body remains eligible for memory.' : 'On application, zero will replace the previous held text input and the journal body will become eligible for memory.'} Other inputs, ordinary dynamics, and separately chosen actions continue.</p>}
  </div>;
}
function Decision({ decision, skipped = false }: { decision: Pick<SustainedActionDecision, 'request' | 'rejection' | 'reservoirInput'>; skipped?: boolean }) {
  return <><p>{actionDescription(decision.request)}</p>{decision.rejection && <p className="my-reservoir-action-rejection">{decision.rejection}</p>}{decision.reservoirInput && <ReservoirInput input={decision.reservoirInput} skipped={skipped}/>}</>;
}

export function ActionReceiptView({ receipt, detailed = false }: { receipt: SustainedActionReceipt; detailed?: boolean }) {
  return <div className={`my-reservoir-action-receipt action-${receipt.status}`}>
    <p><strong>{actionReceiptStatus(receipt)}</strong></p>
    <p>{actionDescription(receipt.request)}</p>
    {receipt.rejection && <p className="my-reservoir-action-rejection">{receipt.rejection}</p>}
    {receipt.reservoirInput && <ReservoirInput input={receipt.reservoirInput} appliedStep={receipt.appliedStep}/>}
    {detailed && <>
      <dl className="my-reservoir-data"><dt>Observed / applied step</dt><dd>{receipt.observedStep} / {receipt.appliedStep}</dd><dt>Attempt</dt><dd>{receipt.attemptId}</dd><dt>Immediate action difference · L2</dt><dd>{number(receipt.stateDeltaL2)}</dd><dt>Largest coordinate difference</dt><dd>{number(receipt.stateDeltaMaxAbs)}</dd><dt>Pulse coordinates clipped</dt><dd>{receipt.clippedCoordinates}</dd></dl>
      <p className="my-reservoir-small">The immediate difference compares the resulting recurrent state with the same step omitting this action, while retaining the previous controls and the same journal feedback and noise. It does not measure the action’s later effect.</p>
      <h5>Controls before this choice</h5><Controls controls={receipt.controlsBefore}/>
      <h5>Controls after this choice</h5><Controls controls={receipt.controlsAfter}/>
    </>}
  </div>;
}

export default function MyReservoirActions({ summary }: { summary: SustainedSummary }) {
  if (!summary.config.actionMode) return null;
  const actions = summary.actions, pending = actions?.pending;
  return <section className="my-reservoir-authored-actions" aria-label="Reservoir shaping">
    <h2>Reservoir shaping</h2>
    <p>The model chooses actions after ordinary entries. Adjustments persist until changed or released; scheduled conversations do not execute actions.</p>
    {summary.config.actionMode === 'authored-v2' && <p>The model can also choose whether an ordinary entry’s text enters numerical input. This is independent of NEXT. Scheduled conversations continue to feed their text back.</p>}
    {actions ? <>
      <h3>Saved controls · through step {actions.durableStep}</h3>
      <Controls controls={actions.state.controls}/>
      <p className="my-reservoir-small">{actions.state.decisionCount} recorded choices · {actions.state.appliedCount} applied actions · {actions.state.rejectedCount} rejected choices</p>
      {pending && <div className="my-reservoir-action-pending" role="status">
        <h3>{pending.durablePrepared ? 'Saved action waiting for application' : 'Action waiting for save confirmation'}</h3>
        <Decision decision={pending.decision}/>
        <p>Entry at step {pending.observedStep}{pending.intendedStep == null ? '' : ` · intended step ${pending.intendedStep}`}. No application has been recorded for this choice.</p>
      </div>}
      {actions.state.latestReceipt ? <><h3>Latest recorded result</h3><ActionReceiptView receipt={actions.state.latestReceipt}/></> : <p>No action result has been recorded yet.</p>}
      {actions.state.recentReceipts.length > 0 && <details className="my-reservoir-details"><summary>Recent action results · {actions.state.recentReceipts.length}</summary><ol className="my-reservoir-action-history">{actions.state.recentReceipts.map(receipt => <li key={`${receipt.journalId}:${receipt.appliedStep}`}><ActionReceiptView receipt={receipt}/></li>)}</ol><p>The current controls and recent results return to ordinary writing independently of the earlier journal selected as memory.</p></details>}
    </> : <p>Waiting for saved action state.</p>}
  </section>;
}

export function JournalActionDetails({ journal }: { journal: SustainedJournal }) {
  if (!journal.action) return null;
  return <section className="my-reservoir-journal-action" aria-label="Journal action">
    <h4>Chosen action</h4>
    {journal.actionReceipt ? <ActionReceiptView receipt={journal.actionReceipt} detailed/> : <>
      <Decision decision={journal.action} skipped={journal.status === 'skipped'}/>
      <p>{journal.status === 'skipped' ? 'The saved action was skipped with this entry’s feedback. No action was applied.' : 'The choice is retained with this entry. No durable action result has been recorded yet.'}</p>
    </>}
    {journal.action.rawTail !== null && <><h5>Exact action line</h5><pre>{journal.action.rawTail}</pre></>}
    {journal.action.reservoirInput?.rawDirective != null && <><h5>Exact text-input directive</h5><pre>{journal.action.reservoirInput.rawDirective}</pre></>}
    <p>{journal.action.reservoirInput ? 'The text-input decision controls whether the journal body becomes numerical feedback. It does not remove the saved writing or change the separate NEXT choice.' : 'The journal body is encoded as feedback separately from the action line.'} The complete received reply remains in Evidence.</p>
    {journal.bodySha256 && <p className="my-reservoir-hash">Journal body SHA-256: {journal.bodySha256}</p>}
  </section>;
}
