import type { ProviderPromptEvaluation } from './myReservoirTypes';

const reasons: Record<string, string> = {
  wrongType: 'the returned value had the wrong type',
  negative: 'the returned count was negative',
  nonInteger: 'the returned count was not an integer',
  outOfRange: 'the returned count exceeded the supported integer range',
  duplicateField: 'the response repeated the count field',
};
function retainedCount(value: ProviderPromptEvaluation | null | undefined): string {
  if (!value) return 'Not retained';
  if (value.status === 'reported' && typeof value.count === 'string' && /^(0|[1-9][0-9]{0,19})$/.test(value.count)
    && BigInt(value.count) <= 18446744073709551615n) return `${value.count} tokens`;
  if (value.status === 'unusable' && Object.hasOwn(reasons, value.reason)) return `Unavailable · ${reasons[value.reason]}`;
  return 'Unavailable · invalid retained metadata';
}
export default function ProviderPromptEvidence({ value, contextTokens }: { value?: ProviderPromptEvaluation | null; contextTokens?: number | null }) {
  return <section className="my-reservoir-prompt-evidence">
    <h4>Provider prompt evidence</h4>
    <dl className="my-reservoir-data">
      <dt>Reported prompt tokens</dt><dd>{retainedCount(value)}</dd>
      <dt>Requested context capacity</dt><dd>{contextTokens == null ? 'No explicit capacity retained' : `${contextTokens} tokens`}</dd>
    </dl>
    <p>The count is reported by the provider. It does not establish that the complete supplied prompt was processed, that every part influenced the writing, or that the journal’s measurement claims are accurate. Requested capacity is a separate setting.</p>
  </section>;
}
