import type { LanguageConfiguration, ActionComparisonKind, ActionSessionSummary, SessionFrame, SessionTurn } from './freshTypes';

export function FreshActionSource({ action, paired = false, comparisonKind = 'components', observationChannel, language }: { action: ActionSessionSummary; paired?: boolean; comparisonKind?: ActionComparisonKind; observationChannel?: string | null; language?: LanguageConfiguration }) {
  const local = action.mode !== 'fixedReplay' && language?.backend === 'ollama';
  if (!action.hasJournal) return <details className="fresh-action-source"><summary>Selected component · numerical experiment</summary><p>{paired ? 'This selected arm belongs to a matched comparison.' : 'One standalone component run.'} No prompt, reply, journal or model request exists in Actions A–C.</p></details>;
  return <details className="fresh-action-source"><summary>Accepted action source · {action.mode === 'fixedReplay' ? 'fixed scripted tape' : local ? 'explicit local model' : 'independent scripted writing'}</summary>
    <p>{paired ? comparisonKind === 'observation' ? 'Observation comparison: two D arms with identical measured trajectory and different context access.' : 'Matched components share external forcing and the numerical clock. Their saved journals, memory and return lanes remain separate.' : 'One standalone component run.'} {local ? 'Each request uses the accepted loopback endpoint and exact configured model.' : 'No model is contacted.'}</p>{local && <dl><dt>Accepted endpoint</dt><dd>{language.endpoint}</dd><dt>Configured model</dt><dd>{language.model}</dd><dt>Context tokens</dt><dd>{language.contextTokens ?? 'Not retained'}</dd></dl>}
    {action.mode === 'fixedReplay' ? <><p>Replies and reference-shaped codec vectors come from a precomputed scripted tape. The current prompt remains inspectable but does not generate the tape reply. Fixed replies cannot show whether memory improves writing.</p>
      {paired && <p>Both arms use the same frozen tape. Their current state and memory do not rewrite its retained packets.</p>}
      {action.replyTape ? <dl><dt>Tape format</dt><dd>{action.replyTape.format}</dd><dt>Origin</dt><dd>{action.replyTape.origin}</dd><dt>Retained packets</dt><dd>{action.replyTape.packetCount}</dd></dl> : <p>No reply tape is reported for this component.</p>}</> : local ? <p>Each opportunity sends this run’s own bounded context to the configured local model. Paired arms retain separate requests and outcomes; a returned response is not evidence of learning or writing benefit.</p> : <p>Each opportunity uses this run’s own observations and available saved memory. Replies follow a deterministic script; they do not demonstrate adaptive model writing.</p>}
    {action.hasMemory && <p>Before each new context, the backend rereads the latest saved local journal. A failed read is retained as a failure; it does not silently use replacement memory.</p>}
    {action.hasChoice && <p>{local ? 'Scheduled WAIT / WRITE choices are returned by the local model under the action contract.' : 'Scheduled WAIT / WRITE choices follow the script or fixed tape.'} A manual WRITE is an explicit human request.</p>}
    {action.hasJournal && <p>{comparisonKind === 'observation' && observationChannel === 'sensoryAndReservoir' ? 'This arm’s context receives sensory measurements plus indexed reservoir coordinates at the observed step.' : 'This arm’s context receives sensory measurements; reservoir coordinates are not included.'} Camera movement and human coordinate selection never change the prompt.</p>}
  </details>;
}

export function FreshTurnEvidence({ turn, action }: { turn: SessionTurn; action: ActionSessionSummary }) {
  const wait = turn.chosenAction === 'WAIT';
  const wrote = turn.chosenAction === 'WRITE_JOURNAL';
  return <div className="fresh-action-evidence">
    <section className="fresh-choice-card" aria-label="Retained action outcome"><span className="eyebrow">OPPORTUNITY {turn.observedStep ?? 'UNKNOWN'}</span><h3>{turn.chosenAction ?? 'No chosen action retained'}</h3>
      <p>{wait ? 'WAIT creates no new journal or application receipt. The previously returned input remains in place.' : wrote ? turn.journalSaved === true ? 'WRITE_JOURNAL has a saved journal receipt.' : 'WRITE_JOURNAL has no successful saved journal receipt.' : 'No successful journal is implied by this outcome.'}</p>
      <dl><dt>Requested action</dt><dd>{turn.requestedAction ?? (action.hasChoice ? 'Choice permitted · no forced action' : 'Not retained')}</dd><dt>Outcome</dt><dd>{turn.status}</dd><dt>Journal entry ID</dt><dd>{turn.journalEntryId ?? 'None retained'}</dd><dt>Journal text SHA-256</dt><dd className="fresh-hash">{turn.journalSha256 ?? 'None retained'}</dd><dt>Application step</dt><dd>{turn.applicationStep ?? 'No application receipt retained'}</dd></dl>
      {action.hasFeedback && !wait && <p>Save and application are separate boundaries. Eligible text returns only when a later numerical step applies it.</p>}
      {!action.hasFeedback && <p>This component does not feed saved journal text back into the reservoir.</p>}
    </section>
    {action.hasMemory && <section className="fresh-memory-card" aria-label="Saved journal memory"><span className="eyebrow">EARLIER SAVED JOURNAL → CURRENT CONTEXT</span><h3>Memory retained at this opportunity</h3>
      {turn.memoryText === null ? <p>{turn.failurePhase === 'memoryRead' ? 'The saved-memory read failed. No memory text was accepted for this opportunity.' : 'No earlier journal text was retained in this opportunity’s context.'}</p> : <><p>{action.mode === 'fixedReplay' ? 'Exact reread journal text in the prepared context. The reply still comes from the fixed tape; this context was not sent to a model.' : turn.backend === 'ollama' ? turn.requestStarted === true ? 'The local-model request is recorded as started. Exact reread journal text is retained in its context; this does not establish successful provider receipt or writing benefit.' : turn.requestStarted === false ? 'Exact reread journal text in a prepared context. No dispatched request is recorded for this opportunity.' : 'Exact reread journal text is retained in the context, but the request-start flag is unavailable; provider exposure is unknown.' : 'Exact reread journal text included in this scripted context. This is evidence of exposure, not evidence that the reply used it well.'}</p><pre>{turn.memoryText}</pre></>}
      <dl><dt>Memory entry</dt><dd>{turn.memoryEntryIds.length ? turn.memoryEntryIds.join(', ') : 'None retained'}</dd><dt>Memory text SHA-256</dt><dd className="fresh-hash">{turn.memoryEntrySha256 ?? 'No accepted memory hash retained'}</dd></dl>
    </section>}
  </div>;
}

export function FreshControllerEvidence({ frame }: { frame: SessionFrame }) {
  return <section className="fresh-control-evidence" aria-label="Sensory retention controller"><div><span className="eyebrow">H · MEASURED FILL → NEXT RETENTION</span><h3>Control at selected step {frame.step}</h3></div>
    <p>The separate sensory field used the current retention below. The controller output applies at the following field update; it does not directly change reservoir coordinates.</p>
    <dl><dt>Measured reduced fill</dt><dd>{frame.fillPercent === null ? 'Unavailable' : `${frame.fillPercent}%`}</dd><dt>Retention used at step {frame.step}</dt><dd>{frame.retentionUsed ?? 'Unavailable'}</dd><dt>Next retention</dt><dd>{frame.nextRetention ?? 'Unavailable'}</dd></dl>
    {frame.control ? <details><summary>Exact retained controller measurement</summary><dl><dt>Error</dt><dd>{frame.control.error}</dd><dt>Integral</dt><dd>{frame.control.integral}</dd><dt>Requested retention</dt><dd>{frame.control.requestedRetention}</dd><dt>Applied controller output</dt><dd>{frame.control.appliedRetention}</dd></dl></details> : <p>No controller measurement is retained at this step.</p>}
    <p className="fresh-small">This finite trajectory can have limited control authority. It does not establish target regulation or a writing benefit.</p>
  </section>;
}
