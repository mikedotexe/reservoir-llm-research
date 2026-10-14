import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { FreshActionSource, FreshControllerEvidence, FreshTurnEvidence } from './FreshActionEvidence';
import { ConfigEditor, FreshJournal } from './FreshExperiments';
import { FreshController } from './freshController';
import { actionStage, DEFAULT_FRESH_CONFIG, freshTitle, selectFreshRecipe, type ActionSessionSummary, type SessionFrame, type SessionTurn } from './freshTypes';

const action: ActionSessionSummary = { stage: 7, mode: 'independentGeneration', hasJournal: true, hasFeedback: true, hasMemory: true, hasChoice: true, hasController: false, latestJournalEntryId: 'entry-2', replyTape: null };
const turn: SessionTurn = { requestOrder: 2, index: 2, id: '3', observedStep: '90', applicationStep: null, status: 'completed', backend: 'scripted', model: null, prompt: 'Exact context', reply: null, encodedFeatures: null, semanticVector: null, failure: null, journalSaved: false, rawReply: '{"action":"WAIT"}', requestedAction: 'WAIT', chosenAction: 'WAIT', contextKind: 'languageRequest', memoryEntryIds: ['entry-2'], journalRelativePath: null, configuredModel: null, providerModel: 'scripted', requestStarted: true, tapePacketId: null, failurePhase: null, memoryText: '<script>stay inert</script>\nEarlier saved text', memoryEntrySha256: 'a'.repeat(64), journalEntryId: null, journalSha256: null };
const frame: SessionFrame = { index: 29, step: '30', time: 10, state: Array(32).fill(.2), input: Array(66).fill(0), noise: Array(32).fill(0), fillPercent: 70, eigenvalues: [2, 1], retentionUsed: .96, nextRetention: .94, semanticTurnId: '1', explorationControls: null, control: { error: -2, integral: .4, requestedRetention: .93, appliedRetention: .94 } };

describe('fresh action recipe and evidence presentation', () => {
  it('keeps original stages separate and clamps both finite settings when switching to Actions', () => {
    const original = { ...DEFAULT_FRESH_CONFIG, steps: 3000, turnEvery: 2500, actionMode: 'fixedReplay' as const };
    const selected = selectFreshRecipe(original, 'actionH');
    expect(selected.steps).toBe(600); expect(selected.turnEvery).toBe(600); expect(selected.actionMode).toBe('fixedReplay'); expect(original.steps).toBe(3000);
    const html = renderToStaticMarkup(<ConfigEditor config={selected} setConfig={() => {}} disabled={false}/>);
    expect(html).toContain('label="Original stages"'); expect(html).toContain('label="Actions A–H"'); expect(html).toContain('value="fixedReplay" selected=""'); expect(html).toContain('fixed replies cannot show whether memory improves writing'); expect(html).toContain('Synthetic input strength'); expect(html).not.toContain('Model endpoint');
  });
  it('retains 0.7 journal aliases and does not expose text controls in Actions A–C', () => {
    expect(actionStage('journalD')).toBe(4); expect(actionStage('journalE')).toBe(5); expect(freshTitle('journalE')).toContain('0.7 recipe'); expect(actionStage('stage4')).toBeNull();
    const html = renderToStaticMarkup(<ConfigEditor config={{ ...DEFAULT_FRESH_CONFIG, recipe: 'actionC' }} setConfig={() => {}} disabled={false}/>);
    expect(html).not.toContain('Turn opportunity every'); expect(html).not.toContain('Reply mode'); expect(html).toContain('No text opportunity');
    expect(renderToStaticMarkup(<FreshActionSource action={{ ...action, stage: 3, hasJournal: false, hasMemory: false }}/>)).not.toContain('independent scripted writing');
  });
  it('shows WAIT and exact memory exposure without inventing a saved journal or feedback application', () => {
    const html = renderToStaticMarkup(<FreshTurnEvidence turn={turn} action={action}/>);
    expect(html).toContain('WAIT creates no new journal or application receipt'); expect(html).toContain('previously returned input remains'); expect(html).toContain('No application receipt retained'); expect(html).toContain('entry-2'); expect(html).toContain('a'.repeat(64)); expect(html).toContain('&lt;script&gt;stay inert&lt;/script&gt;'); expect(html).not.toContain('<script>'); expect(html).toContain('evidence of exposure'); expect(html).not.toContain('has a saved journal receipt');
  });
  it('keeps fixed tape source separate from reread memory and an actual request', () => {
    const fixed = { ...action, mode: 'fixedReplay' as const, replyTape: { format: 'essentials-action-tape-v1', origin: 'scripted-reference', packetCount: 600 } };
    const html = renderToStaticMarkup(<><FreshActionSource action={fixed}/><FreshTurnEvidence turn={{ ...turn, requestStarted: false, tapePacketId: '90' }} action={fixed}/></>);
    expect(html).toContain('essentials-action-tape-v1'); expect(html).toContain('reference-shaped codec vectors'); expect(html).toContain('context was not sent to a model'); expect(html).toContain('Fixed replies cannot show whether memory improves writing');
  });
  it('distinguishes a failed memory read from absent earlier memory, and D from feedback eligibility', () => {
    const failed = { ...turn, chosenAction: null, requestOrder: null, memoryText: null, memoryEntrySha256: null, failurePhase: 'memoryRead' };
    const html = renderToStaticMarkup(<FreshTurnEvidence turn={failed} action={action}/>);
    expect(html).toContain('saved-memory read failed'); expect(html).toContain('No accepted memory hash retained'); expect(html).not.toContain('Earlier saved text');
    const saved = renderToStaticMarkup(<FreshTurnEvidence turn={{ ...turn, chosenAction: 'WRITE_JOURNAL', journalSaved: true, journalEntryId: 'entry-3', journalSha256: 'b'.repeat(64) }} action={{ ...action, stage: 4, hasFeedback: false, hasMemory: false }}/>);
    expect(saved).toContain('has a saved journal receipt'); expect(saved).toContain('does not feed saved journal text back'); expect(saved).not.toContain('Saved journal memory');
  });
  it('treats failed-save entry identity as retained evidence rather than successful storage', () => {
    const html = renderToStaticMarkup(<FreshTurnEvidence turn={{ ...turn, requestedAction: null, chosenAction: 'WRITE_JOURNAL', journalSaved: false, status: 'failed', failurePhase: 'journalSave', journalEntryId: 'failed-entry', journalSha256: 'c'.repeat(64) }} action={action}/>);
    expect(html).toContain('no successful saved journal receipt'); expect(html).toContain('Journal entry ID'); expect(html).toContain('Journal text SHA-256'); expect(html).toContain('failed-entry'); expect(html).not.toContain('Saved text SHA-256'); expect(html).not.toContain('Saved entry'); expect(html).toContain('Choice permitted · no forced action');
  });
  it('separates current retention from next-step controller output and preserves missing measurements', () => {
    const html = renderToStaticMarkup(<FreshControllerEvidence frame={frame}/>);
    expect(html).toContain('Retention used at step 30'); expect(html).toContain('0.96'); expect(html).toContain('Next retention'); expect(html).toContain('0.94'); expect(html).toContain('0.93'); expect(html).toContain('does not directly change reservoir coordinates');
    const missing = renderToStaticMarkup(<FreshControllerEvidence frame={{ ...frame, control: null, nextRetention: null }}/>);
    expect(missing).toContain('No controller measurement'); expect(missing).not.toContain('Applied controller output'); expect(missing).toContain('Unavailable');
  });
  it('uses backend manual opportunity capability and preserves independent turn/frame selection', () => {
    const controller = new FreshController();
    const state = { ...controller.snapshot(), summary: { sessionId: 's', generation: '1', revision: '8', config: { ...DEFAULT_FRESH_CONFIG, recipe: 'actionG' as const }, phase: 'paused' as const, step: 91, durableStep: 91, stepLimit: 120, frameCount: 91, turnCount: 3, journalCount: 2, unsavedRecord: true, pendingWrites: false, canStep: true, canRun: true, canExport: true, canRequestJournal: false, saveError: null, libraryEntryId: null, diagnostics: [], explorationControls: null, action, tracks: [{ id: 'right' as const, label: 'Current', stage: 7, frameCount: 91, turnCount: 3, journalCount: 2, status: 'stopped', failure: null, observationChannel: 'sensory', action }] }, turn, turnRevision: '7' };
    const html = renderToStaticMarkup(<FreshJournal state={state} controller={controller}/>);
    expect(html).toContain('<button disabled="">Request manual WRITE'); expect(html).toContain('frame navigation does not change this text selection'); expect(html).toContain('Retained WAIT reply · no journal'); expect(html).toContain('Exact dispatched request context');
    const ready = renderToStaticMarkup(<FreshJournal state={{ ...state, summary: { ...state.summary, canRequestJournal: true } }} controller={controller}/>);
    expect(ready).toContain('<button>Request manual WRITE');
    const unknown = renderToStaticMarkup(<FreshJournal state={{ ...state, turn: { ...turn, requestStarted: null } }} controller={controller}/>);
    expect(unknown).toContain('request-start flag unavailable'); expect(unknown).not.toContain('Prepared context · no request started');
  });
});
