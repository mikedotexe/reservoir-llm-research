import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import FreshFrameViews, { FreshTrackStatus } from './FreshFrameViews';
import { FreshActionSource } from './FreshActionEvidence';
import { ConfigEditor, FreshJournal, FreshRecovery, FreshRecoveryBoundary } from './FreshExperiments';
import { FreshController } from './freshController';
import { DEFAULT_CAMERA } from './types';
import { DEFAULT_FRESH_CONFIG, selectActionComparison, selectFreshRecipe, type ActionSessionSummary, type RecoveryCheckpoint, type SessionFrame, type SessionSummary, type SessionTrackSummary } from './freshTypes';

const action = (stage: number): ActionSessionSummary => ({ stage, mode: 'independentGeneration', hasJournal: stage >= 4, hasFeedback: stage >= 5, hasMemory: stage >= 6, hasChoice: stage >= 7, hasController: stage === 8, latestJournalEntryId: null, replyTape: null });
const track = (id: 'left' | 'right', stage: number): SessionTrackSummary => ({ id, label: id === 'left' ? 'Previous F' : 'Current G', stage, frameCount: 2, turnCount: 1, journalCount: 1, status: 'stopped', failure: null, observationChannel: 'sensory', action: action(stage) });
const summary: SessionSummary = { sessionId: 'pair', generation: '1', revision: '8', config: { ...DEFAULT_FRESH_CONFIG, recipe: 'actionG', actionComparePrevious: true }, phase: 'awaitingJournalSave', step: 2, durableStep: 1, stepLimit: 120, frameCount: 2, turnCount: 1, journalCount: 1, unsavedRecord: true, pendingWrites: false, canStep: false, canRun: false, canExport: false, canRequestJournal: false, action: action(7), tracks: [track('left', 6), track('right', 7)], explorationControls: null, saveError: null, libraryEntryId: null, diagnostics: [] };
const frame = (value: number): SessionFrame => ({ index: 1, step: '2', time: 2 / 3, state: Array(32).fill(value), input: Array(66).fill(0), noise: Array(32).fill(0), eigenvalues: [2, 1], fillPercent: 40, retentionUsed: .955, nextRetention: null, semanticTurnId: null, explorationControls: null, control: null });
describe('fresh comparison presentation', () => {
  it('forces observation D/D and independent context then resets forcing when choosing another component', () => {
    const observed = selectActionComparison({ ...DEFAULT_FRESH_CONFIG, recipe: 'actionH', actionMode: 'fixedReplay' }, 'observation');
    expect(observed.recipe).toBe('actionD'); expect(observed.actionComparePrevious).toBe(true); expect(observed.actionMode).toBe('independentGeneration');
    const html = renderToStaticMarkup(<ConfigEditor config={observed} setConfig={() => {}} disabled={false}/>);
    expect(html).toContain('Observation comparison · D / D'); expect(html).toContain('Prepare quiet inputs'); expect(html).toContain('Prepare active inputs'); expect(html).toContain('No accuracy or learning benefit is implied');
    const changed = selectFreshRecipe({ ...observed, actionForcingProfile: 'continuousSensoryV1' }, 'actionA'); expect(changed.actionComparisonKind).toBe('components'); expect(changed.actionComparePrevious).toBe(false); expect(changed.actionForcingProfile).toBe('pulsedSensoryV1');
    expect(renderToStaticMarkup(<ConfigEditor config={changed} setConfig={() => {}} disabled={false}/>)).toContain('value="components" disabled=""');
  });
  it('labels observation prompt access per arm without attributing viewer choices to prompts', () => {
    const left = renderToStaticMarkup(<FreshActionSource action={action(4)} paired comparisonKind="observation" observationChannel="sensory"/>);
    const right = renderToStaticMarkup(<FreshActionSource action={action(4)} paired comparisonKind="observation" observationChannel="sensoryAndReservoir"/>);
    expect(left).toContain('reservoir coordinates are not included'); expect(right).toContain('plus indexed reservoir coordinates at the observed step'); expect(right).not.toContain('reservoir coordinates are not included'); expect(right).toContain('human coordinate selection never change the prompt');
    const fixed = renderToStaticMarkup(<FreshActionSource action={{ ...action(6), mode: 'fixedReplay' }} paired/>);
    expect(fixed).toContain('Both arms use the same frozen tape'); expect(fixed).toContain('Fixed replies cannot show whether memory improves writing');
  });
  it('shows retained failures and unresolved pair meaning without calling stopped records complete', () => {
    const html = renderToStaticMarkup(<FreshTrackStatus summary={{ ...summary, tracks: [{ ...summary.tracks[0], status: 'failed', failure: 'Read failed' }, { ...summary.tracks[1], failure: 'Peer action cancelled' }] }} selected="right" onSelect={() => {}}/>);
    expect(html).toContain('unresolved or failed arm does not establish a completed pair'); expect(html).toContain('Read failed'); expect(html).toContain('Peer action cancelled'); expect(html).toContain('Retained outcome'); expect(html).toContain('Inspect Previous F');
  });
  it('keeps paired surfaces aligned and exact table/fill tied to the selected track', () => {
    const html = renderToStaticMarkup(<FreshFrameViews summary={summary} frames={{ left: frame(-.25), right: frame(.75) }} selected="left" node={0} pose={DEFAULT_CAMERA} onPose={() => {}} onSelectTrack={() => {}} onSelectNode={() => {}} tableOnly active/>);
    expect(html).toContain('linked cameras'); expect(html).toContain('Previous F · 32-node reservoir'); expect(html).toContain('Current G · 32-node reservoir'); expect(html).toContain('EXACT SELECTED TRACK · Previous F'); expect(html).toContain('Previous F track at step 2'); expect(html).toContain('-0.25'); expect(html).not.toContain('<canvas');
  });
  it('names a right pending journal even when the selected left component has no text channel', () => {
    const controller = new FreshController(), state = { ...controller.snapshot(), selectedTrack: 'left' as const, summary: { ...summary, config: { ...summary.config, recipe: 'actionD' as const }, action: action(4), tracks: [{ ...track('left', 3), label: 'Previous C', turnCount: 0, journalCount: 0 }, { ...track('right', 4), label: 'Current D' }] }, pendingJournal: { arm: 'right' as const, id: 'same-entry', actionId: 1, observedStep: 2, prompt: 'right context', text: 'right candidate', sha256: 'a'.repeat(64), relativePath: 'right/same-entry.json' } };
    const html = renderToStaticMarkup(<FreshJournal state={state} controller={controller}/>);
    expect(html).toContain('No text channel on this component'); expect(html).toContain('Pending right journal'); expect(html).toContain('Save right journal'); expect(html).toContain('Selected track has no text opportunities'); expect(html).not.toContain('Stage turns retain');
  });
  it('keeps half-resolved recovery receipts distinct from portable pair verification and distinguishes equal IDs by arm', () => {
    const controller = new FreshController();
    const checkpoint: RecoveryCheckpoint = { schema: 'checkpoint', sessionId: 'pair', generation: '1', revision: '9', config: {}, phase: 'awaitingJournalSave', step: 30, durableStep: 29, recordSha256: null, pendingJournal: null, updatedAtMs: '100', discarded: false, attempts: [{ arm: 'left', number: 1, entryId: 'same', atMs: '99', status: 'committed', diagnostic: null }, { arm: 'right', number: 2, entryId: 'same', atMs: '100', status: 'failed', diagnostic: 'Full disk' }], pairedBoundary: { step: 30, arms: [{ arm: 'left', stage: 5, receipt: { id: 1, observedStep: 30, status: 'completed', chosenAction: 'WRITE_JOURNAL', journalEntryID: 'same', saveReceipt: { status: 'saved', sha256: 'a'.repeat(64) }, memoryText: '<script>inert</script>' }, journal: { id: 'same', sha256: 'a'.repeat(64), text: 'left retained text' } }, { arm: 'right', stage: 6, receipt: null, journal: null }] } };
    const html = renderToStaticMarkup(<FreshRecoveryBoundary checkpoint={checkpoint}/>);
    expect(html).toContain('not a numerically verified portable pair'); expect(html).toContain('snapshot ends at step 29'); expect(html).toContain('left arm · component E'); expect(html).toContain('right arm · component F'); expect(html).toContain('No finalized action receipt'); expect(html).toContain('left retained text'); expect(html).toContain('&lt;script&gt;'); expect(html).not.toContain('<script>');
    const recovery = renderToStaticMarkup(<FreshRecovery state={{ ...controller.snapshot(), recovered: checkpoint }} controller={controller}/>);
    expect(recovery).toContain('left · same'); expect(recovery).toContain('right · same'); expect(recovery).not.toContain('Resume experiment');
  });
});
