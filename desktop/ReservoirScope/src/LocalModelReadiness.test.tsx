import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { ConfigEditor, FreshLanguageBoundary, FreshRecovery } from './FreshExperiments';
import { FreshActionSource, FreshTurnEvidence } from './FreshActionEvidence';
import LocalModelReadiness, { ModelReadinessEvidence } from './LocalModelReadiness';
import { FreshController, type FreshState } from './freshController';
import { DEFAULT_FRESH_CONFIG, type ActionSessionSummary, type PendingLanguage, type SessionTurn } from './freshTypes';
import { languageKey } from './localModelController';

const language = { backend: 'ollama' as const, endpoint: 'http://127.0.0.1:11435', model: 'exact:tag', contextTokens: 4096, responseFormat: 'json' as const };
const action: ActionSessionSummary = { stage: 7, mode: 'independentGeneration', hasJournal: true, hasFeedback: true, hasMemory: true, hasChoice: true, hasController: false, latestJournalEntryId: null, replyTape: null };
const pending: PendingLanguage = { operationId: 'op-1', arm: 'left', turnId: 2, observedStep: 30, endpoint: language.endpoint, model: language.model, state: 'requesting' };
function state(): FreshState {
  return { ...new FreshController().snapshot(), summary: { sessionId: 's', generation: '1', revision: '30', config: { ...DEFAULT_FRESH_CONFIG, recipe: 'actionG', language }, phase: 'awaitingLanguage', step: 30, durableStep: 29, stepLimit: 120, frameCount: 30, turnCount: 1, journalCount: 1, unsavedRecord: true, pendingWrites: false, canStep: false, canRun: false, canExport: false, saveError: null, libraryEntryId: null, diagnostics: [], explorationControls: null, canRequestJournal: false, action, tracks: [], pendingLanguage: pending } };
}
describe('explicit readiness and pending model presentation', () => {
  it('shows explicit contact controls and fixed request bounds without claiming automatic readiness', () => {
    const html = renderToStaticMarkup(<ConfigEditor config={{ ...DEFAULT_FRESH_CONFIG, recipe: 'actionG', language }} disabled={false} setConfig={() => {}}/>);
    expect(html).toContain('Check local model'); expect(html).toContain('60-second'); expect(html).toContain('256-token'); expect(html).toContain('JSON action reply'); expect(html).not.toContain('Model available');
    expect(renderToStaticMarkup(<LocalModelReadiness configuration={language} disabled={false}/>)).not.toContain('readiness receipt');
  });
  it('availability receipts expose exact identity and explicitly do not qualify generation or capacity', () => {
    const html = renderToStaticMarkup(<ModelReadinessEvidence state={{ key: languageKey(language), checking: false, error: '', message: '', result: { requestId: 'r', operationId: 'op', endpoint: language.endpoint, requestedModel: language.model, status: 'found', matchedModel: 'exact:tag', digest: 'sha256:test', checkedAtMs: '123', diagnostic: '<script>inert</script>' } }}/>);
    expect(html).toContain('sha256:test'); expect(html).toContain('does not guarantee enough memory or a successful response'); expect(html).toContain('&lt;script&gt;'); expect(html).not.toContain('<script>');
  });
  it('names pending arm and held clock while separating Pause from explicit cancellation', () => {
    const html = renderToStaticMarkup(<FreshLanguageBoundary state={state()} controller={new FreshController()}/>);
    expect(html).toContain('LEFT ARM'); expect(html).toContain('clock is held'); expect(html).toContain('already dispatched request may finish'); expect(html).toContain('Cancel request and stop'); expect(html).toContain('not a saved journal or applied feedback');
  });
  it('shows compatibility blocking as no active request rather than an endless generating status', () => {
    const s = state(); s.summary!.pendingLanguage = { ...pending, state: 'compatibilityBlocked' };
    const html = renderToStaticMarkup(<FreshLanguageBoundary state={s} controller={new FreshController()}/>); expect(html).toContain('Response acceptance blocked'); expect(html).toContain('No network request is active'); expect(html).not.toContain('Local model request in progress'); expect(html).toContain('Stop and retain blocked outcome');
  });
  it('source and memory descriptions use actual local provenance without scripted or benefit claims', () => {
    const html = renderToStaticMarkup(<FreshActionSource action={action} language={language} paired/>);
    expect(html).toContain('explicit local model'); expect(html).not.toContain('No model is contacted'); expect(html).not.toContain('Replies follow a deterministic script'); expect(html).toContain('separate requests and outcomes');
    const turn = { backend: 'ollama', requestStarted: true, chosenAction: 'WAIT', journalSaved: false, status: 'completed', memoryEntryIds: ['m1'], memoryText: 'retained memory', memoryEntrySha256: 'a'.repeat(64) } as unknown as SessionTurn;
    const text = renderToStaticMarkup(<FreshTurnEvidence action={action} turn={turn}/>); expect(text).toContain('local-model request is recorded as started'); expect(text).toContain('does not establish successful provider receipt'); expect(text).toContain('WAIT creates no new journal');
    const prepared = renderToStaticMarkup(<FreshTurnEvidence action={action} turn={{ ...turn, requestStarted: false }}/>); expect(prepared).toContain('No dispatched request is recorded'); expect(prepared).not.toContain('evidence of exposure');
  });
  it('recovery treats an unresolved provider request as inert metadata with no resubmission', () => {
    const controller = new FreshController(); const s = { ...state(), recovered: { schema: 'checkpoint', sessionId: 's', generation: '1', revision: '30', config: {}, phase: 'awaitingLanguage', step: 30, durableStep: 29, recordSha256: 'a'.repeat(64), pendingJournal: null, pendingLanguage: { ...pending, prompt: '<script>do not run</script>', requestStarted: true }, attempts: [], updatedAtMs: '100', discarded: false } };
    const html = renderToStaticMarkup(<FreshRecovery state={s} controller={controller}/>); expect(html).toContain('Unresolved provider boundary'); expect(html).toContain('never resubmitted'); expect(html).toContain('&lt;script&gt;'); expect(html).not.toContain('Resume request');
    expect(html).toContain('No received response is retained');
  });
  it.each(['pendingLanguage', 'rejectedLanguage'] as const)('renders %s response evidence without promoting it into an accepted journal', key => {
    const s: FreshState = { ...state(), recovered: { schema: 'checkpoint', sessionId: 's', generation: '1', revision: '31', config: {}, phase: key === 'rejectedLanguage' ? 'stopped' : 'awaitingLanguage', step: 30, durableStep: 29, recordSha256: 'a'.repeat(64), pendingJournal: null, [key]: { ...pending, state: 'compatibilityBlocked', prompt: '<script>prompt</script>', requestStarted: true, diagnostic: 'Unqualified response <b>reason</b>', receivedResponse: { text: '<script>untrusted reply</script>', textByteCount: 90000, textSha256: 'b'.repeat(64), textTruncated: true, providerModel: '<model>', stopReason: 'stop', metadataTruncated: true, tokenCount: 22, complete: true } }, attempts: [], updatedAtMs: '100', discarded: false } };
    const html = renderToStaticMarkup(<FreshRecovery state={s} controller={new FreshController()}/>);
    expect(html).toContain(key === 'rejectedLanguage' ? 'Rejected provider response retained after Stop' : 'Unresolved provider boundary');
    expect(html).toContain('not accepted by the engine'); expect(html).toContain('90000'); expect(html).toContain('b'.repeat(64)); expect(html).toContain('only a UTF-8 prefix'); expect(html).toContain('metadata was truncated');
    expect(html).toContain('&lt;script&gt;untrusted reply&lt;/script&gt;'); expect(html).toContain('&lt;b&gt;reason&lt;/b&gt;'); expect(html).not.toContain('<script>'); expect(html).not.toContain('Full received text');
    expect(html).toContain('no saved journal or feedback eligibility'); expect(html).not.toContain('Resume request');
  });
  it('distinguishes full rejected text from absent response evidence and legacy checkpoints', () => {
    const base = { schema: 'checkpoint', sessionId: 's', generation: '1', revision: '31', config: {}, phase: 'stopped', step: 30, durableStep: 29, recordSha256: 'a'.repeat(64), pendingJournal: null, attempts: [], updatedAtMs: '100', discarded: false };
    const controller = new FreshController();
    const legacy = renderToStaticMarkup(<FreshRecovery state={{ ...state(), recovered: base }} controller={controller}/>);
    expect(legacy).not.toContain('Rejected provider'); expect(legacy).not.toContain('Unresolved provider');
    const full = renderToStaticMarkup(<FreshRecovery state={{ ...state(), recovered: { ...base, rejectedLanguage: { ...pending, receivedResponse: { text: 'Exact rejected text', textByteCount: 19, textSha256: 'c'.repeat(64), textTruncated: false, providerModel: null, stopReason: null, metadataTruncated: false, tokenCount: null, complete: false } } } }} controller={controller}/>);
    expect(full).toContain('Full received text is retained below'); expect(full).toContain('Exact rejected text'); expect(full).toContain('Not retained'); expect(full).not.toContain('Text truncated');
  });
});
