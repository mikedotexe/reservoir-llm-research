import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import ProviderPromptEvidence from './ProviderPromptEvidence';
import { MyReservoirJournalDetail } from './MyReservoirJournals';
import { journal } from './myReservoirTestFixtures';
import type { ProviderPromptEvaluation } from './myReservoirTypes';

describe('provider-reported prompt evidence', () => {
  it.each(['0', '9007199254740993', '18446744073709551615'])('preserves exact count %s separately from requested capacity', count => {
    const html = renderToStaticMarkup(<ProviderPromptEvidence value={{ status: 'reported', count }} contextTokens={8192}/>);
    expect(html).toContain(`<dt>Reported prompt tokens</dt><dd>${count} tokens</dd>`);
    expect(html).toContain('<dt>Requested context capacity</dt><dd>8192 tokens</dd>');
    expect(html).toContain('It does not establish that the complete supplied prompt was processed');
    expect(html).toContain('journal’s measurement claims are accurate');
  });
  it.each([undefined, null])('does not invent a count for absent legacy metadata', value => {
    const html = renderToStaticMarkup(<ProviderPromptEvidence value={value}/>);
    expect(html).toContain('<dt>Reported prompt tokens</dt><dd>Not retained</dd>');
    expect(html).toContain('No explicit capacity retained');
    expect(html).not.toContain('0 tokens');
  });
  it.each(['wrongType', 'negative', 'nonInteger', 'outOfRange', 'duplicateField'] as const)('explains unusable %s metadata', reason => {
    const html = renderToStaticMarkup(<ProviderPromptEvidence value={{ status: 'unusable', reason }}/>);
    expect(html).toContain('<dd>Unavailable · ');
    expect(html).not.toContain('invalid retained metadata');
  });
  it.each(['18446744073709551616', '1.5', '-1', '01', '1e3', '<script>'])('rejects malformed IPC count %s without number coercion', count => {
    const html = renderToStaticMarkup(<ProviderPromptEvidence value={{ status: 'reported', count }}/>);
    expect(html).toContain('Unavailable · invalid retained metadata');
    expect(html).not.toContain('<script>');
  });
  it('keeps per-entry metadata inside closed Evidence and never transfers it to an old entry', () => {
    const render = (value?: ProviderPromptEvaluation) => renderToStaticMarkup(<MyReservoirJournalDetail journal={{ ...journal(), providerPromptEvaluation: value }} revision="1"/>);
    const [prose, evidence] = render({ status: 'reported', count: '9007199254740993' }).split('<details class="my-reservoir-journal-evidence">');
    expect(prose).not.toContain('9007199254740993');
    expect(evidence).toContain('9007199254740993 tokens');
    expect(render()).not.toContain('9007199254740993');
    expect(render()).toContain('<dt>Reported prompt tokens</dt><dd>Not retained</dd>');
    expect(render()).not.toContain('<details open');
  });
});
