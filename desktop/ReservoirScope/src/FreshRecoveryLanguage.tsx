const object = (value: unknown): Record<string, unknown> => value !== null && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
const text = (value: unknown): string => typeof value === 'string' ? value : typeof value === 'boolean' || typeof value === 'number' && Number.isFinite(value) ? String(value) : 'Not retained';

/** Checkpoint text is inert evidence, never an executable prompt or resumable request. */
export default function FreshRecoveryLanguage({ boundary, rejected = false }: { boundary: unknown; rejected?: boolean }) {
  const retained = object(boundary), response = object(retained.receivedResponse), hasResponse = retained.receivedResponse != null;
  return <details open className="fresh-recovery-language"><summary>{rejected ? 'Rejected provider response retained after Stop' : 'Unresolved provider boundary · no automatic resume'}</summary>
    <p>This is retained checkpoint evidence, separate from the portable record. It is never resubmitted from recovery and establishes no saved journal or feedback eligibility.</p>
    {retained.state === 'prepared' && <p>This checkpoint may predate a later dispatch. It does not establish whether the provider received a request after the checkpoint was saved.</p>}
    <dl>{(['operationId', 'arm', 'turnId', 'observedStep', 'state', 'endpoint', 'model', 'requestStarted'] as const).map(key => <div key={key}><dt>{key}</dt><dd>{text(retained[key])}</dd></div>)}</dl>
    {typeof retained.diagnostic === 'string' && <p className="fresh-error">{retained.diagnostic}</p>}
    <details><summary>Exact retained prompt</summary><pre>{text(retained.prompt)}</pre></details>
    {hasResponse ? <section><h4>Received response · not accepted by the engine</h4><p>The retained completeness flag does not qualify this text as a valid action, journal or semantic input.</p>
      <dl><dt>Original text byte count</dt><dd>{text(response.textByteCount)}</dd><dt>SHA-256 of original text</dt><dd className="fresh-hash">{text(response.textSha256)}</dd><dt>Returned model identity</dt><dd>{text(response.providerModel)}</dd><dt>Stop reason</dt><dd>{text(response.stopReason)}</dd><dt>Token count</dt><dd>{text(response.tokenCount)}</dd><dt>Retained completeness flag</dt><dd>{text(response.complete)}</dd></dl>
      <p>{response.textTruncated === true ? 'Text truncated: only a UTF-8 prefix of at most 64 KiB is retained below. The byte count and SHA-256 describe the original text.' : response.textTruncated === false ? 'Full received text is retained below.' : 'Text coverage flag not retained; completeness is unknown.'}</p>
      {response.metadataTruncated === true && <p>Returned model or stop-reason metadata was truncated; the displayed labels are retained prefixes.</p>}
      <pre>{text(response.text)}</pre>
    </section> : <p>No received response is retained in this checkpoint.</p>}
  </details>;
}
