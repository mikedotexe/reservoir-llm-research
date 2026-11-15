import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import MyReservoirActions, { ActionReceiptView, JournalActionDetails } from './MyReservoirActions';
import MyReservoirConfig from './MyReservoirConfig';
import MyReservoirInquiry from './MyReservoirInquiry';
import { MyReservoirJournalDetail } from './MyReservoirJournals';
import { ACTION_JOURNAL_PROMPT, ACTION_JOURNAL_PROMPT_V1, CONTINUITY_JOURNAL_PROMPT, validActionSummary, validAuthoredActionConfig, validJournalAction, withAuthoredActionMode, withAuthoredActions } from './authoredActions';
import { validInquiryDecision, validInquiryReceipt, validProbeVector } from './localInquiries';
import { DEFAULT_CHECK_IN_SCHEDULE } from './checkInSchedule';
import { DEFAULT_SUSTAINED_CONFIG, type SustainedActionDecision, type SustainedActionReceipt, type SustainedConfig, type SustainedContinuityState, type SustainedInquiryDecision, type SustainedInquiryReceipt, type SustainedJournal } from './myReservoirTypes';
import { journal, reservoirFixture, reservoirSummary, settle } from './myReservoirTestFixtures';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true }));

const config: SustainedConfig = { ...DEFAULT_SUSTAINED_CONFIG, actionMode: 'authored-v3', promptVersion: CONTINUITY_JOURNAL_PROMPT };
const controls = { leak: .65, recurrentGain: 1, feedbackScale: .4 };
const input = { disposition: 'withhold' as const, rawDirective: 'WITHHOLD_RESERVOIR_INPUT=true', rejection: null };
const question = 'What changed after my <probe>?';
const inquiry: SustainedInquiryDecision = { rawDirective: `INQUIRY: OPEN both ${JSON.stringify(question)}`, request: { kind: 'open', source: 'both', question }, rejection: null };
const inquiryReceipt: SustainedInquiryReceipt = { journalId: 'journal-1', appliedStep: 4, status: 'opened', inquiryId: 'inquiry-4', previousInquiryId: null, rejection: null, decision: inquiry };
const vector = [0.5, ...Array<number>(47).fill(0)];
const decision: SustainedActionDecision = { body: 'I will follow this change.', rawTail: `NEXT: PROBE ${JSON.stringify(vector)}`, request: { kind: 'probe', vector }, rejection: null, reservoirInput: input, inquiry };
const receipt: SustainedActionReceipt = { journalId: 'journal-1', attemptId: 1, observedStep: 3, appliedStep: 4, status: 'applied', request: decision.request, rawTail: decision.rawTail, rejection: null, reservoirInput: input, inquiry: inquiryReceipt, probe: { requestedVector: vector, appliedVector: [...vector], stateDeltaVector: [0.1, ...Array<number>(31).fill(0)] }, controlsBefore: controls, controlsAfter: controls, stateDeltaL2: .1, stateDeltaMaxAbs: .1, clippedCoordinates: 0 };
const excerpt = { journalId: 'older', observedStep: 1, appliedStep: 2, bodySha256: 'a'.repeat(64), bodyBytes: 800, excerpt: '<script>Reference text</script>', excerptTruncated: true, checkIn: false };
const continuity = (): SustainedContinuityState => ({ meaningfulReceipts: [receipt], inputTransitions: [{ journalId: 'journal-1', appliedStep: 4, disposition: 'withhold' }], journalWindow: [{ ...excerpt }], activeInquiry: { id: 'inquiry-4', question, source: 'both', openedJournalId: 'journal-1', openedObservedStep: 3, openedAppliedStep: 4, lastContinuedStep: 4, continuationCount: 0, baseline: { step: 3, rms: .2, sensoryFill: 70, state: Array<number>(32).fill(.2) }, openingControls: controls, history: [{ ...excerpt }] }, latestInquiryReceipt: inquiryReceipt });
const summary = () => reservoirSummary({ config, step: 4, durableStep: 4, actions: { state: { controls, latestReceipt: receipt, recentReceipts: [receipt], decisionCount: 1, appliedCount: 1, rejectedCount: 0, continuity: continuity() }, durableStep: 4 } });

describe('versioned continuing local inquiry', () => {
  it('selects v3 for newly enabled actions and keeps both previous baselines selectable', async () => {
    expect(withAuthoredActions(DEFAULT_SUSTAINED_CONFIG, true, DEFAULT_SUSTAINED_CONFIG.promptVersion)).toEqual({ ...config, controlFeedback: 'diagnostic-v1' });
    expect(validAuthoredActionConfig(config)).toBe(true);
    for (const [mode, prompt] of [['authored-v1', ACTION_JOURNAL_PROMPT_V1], ['authored-v2', ACTION_JOURNAL_PROMPT]] as const) {
      const earlier = withAuthoredActionMode(config, mode);
      expect(earlier.promptVersion).toBe(prompt);
      expect(validAuthoredActionConfig(earlier)).toBe(true);
    }
    expect(validAuthoredActionConfig({ ...config, promptVersion: ACTION_JOURNAL_PROMPT })).toBe(false);
    const fixture = reservoirFixture();
    expect(await fixture.controller.create(config)).toBe(true);
    const html = renderToStaticMarkup(<MyReservoirConfig config={{ ...config, checkInSchedule: DEFAULT_CHECK_IN_SCHEDULE }} setConfig={() => {}} disabled={false}/>);
    expect(html).toContain('Continuing inquiry and reservoir actions');
    expect(html).toContain('Earlier actions and input choice');
    expect(html).toContain('An inquiry is an opportunity to investigate');
    expect(html).toContain('Ordinary journal turns retain');
    expect(html).toContain('Inquiry directives in a check-in also stay ordinary writing');
  });

  it('shows a saved question and bounded evidence without interpreting authored HTML', async () => {
    expect(validActionSummary(summary())).toBe(true);
    const fixture = reservoirFixture();
    await fixture.controller.create(config); await fixture.controller.connect(); await settle();
    fixture.push({ ...summary(), phase: 'paused' });
    expect(fixture.controller.snapshot().error).toBe('');
    const html = renderToStaticMarkup(<MyReservoirActions summary={fixture.controller.snapshot().summary!}/>);
    expect(html).toContain('What changed after my &lt;probe&gt;?');
    expect(html).toContain('bounded local reading, not a search of the full archive');
    expect(html).toContain('&lt;script&gt;Reference text&lt;/script&gt;');
    expect(html).not.toContain('<script>Reference text</script>');
    expect(html).toContain('Excerpt truncated');
    expect(html).toContain('Retained interventions · 1');
    expect(html).toContain('Retained text-input changes · 1');
    expect(html).toContain('Retaining a question does not mean it has been resolved.');
  });

  it('keeps a pending replacement distinct from the currently applied question', () => {
    const s = summary();
    s.actions!.pending = { entryId: 'journal-2', attemptId: 2, observedStep: 4, phase: 'saving', durablePrepared: false, decision: { request: { kind: 'none' }, rejection: null, reservoirInput: input, inquiry: { ...inquiry, request: { kind: 'open', source: 'journal', question: 'A pending replacement.' } } } };
    expect(validActionSummary(s)).toBe(true);
    const html = renderToStaticMarkup(<MyReservoirActions summary={s}/>);
    expect(html).toContain('Inquiry choice awaiting application');
    expect(html).toContain('A pending replacement.');
    expect(html).toContain('What changed after my &lt;probe&gt;?');
    expect(html).toContain('retained inquiry changes only after');
  });

  it('accepts refreshed later history while preserving the opening baseline', () => {
    const s = summary(), c = s.actions!.state.continuity!;
    s.step = s.durableStep = s.actions!.durableStep = 10;
    c.activeInquiry!.lastContinuedStep = 10;
    c.activeInquiry!.continuationCount = 1;
    c.activeInquiry!.history = [{ ...excerpt, journalId: 'later', observedStep: 6, appliedStep: 7 }];
    expect(validActionSummary(s)).toBe(true);
    const html = renderToStaticMarkup(<MyReservoirInquiry continuity={c}/>);
    expect(html).toContain('Opening observation · step 3');
    expect(html).toContain('latest explicit continuation, at step 10');
    expect(html).toContain('Observed step 6');
  });

  it('records closed and rejected inquiries without claiming a completed investigation', () => {
    const c = continuity(); c.activeInquiry = null;
    c.latestInquiryReceipt = { ...inquiryReceipt, status: 'closed', inquiryId: null, previousInquiryId: 'inquiry-4', decision: { rawDirective: 'INQUIRY: CLOSE', request: { kind: 'close' }, rejection: null } };
    const html = renderToStaticMarkup(<MyReservoirInquiry continuity={c}/>);
    expect(html).toContain('Inquiry closed at step 4');
    expect(html).toContain('does not establish that the question was answered');
    expect(html).toContain('No question is currently retained');
  });

  it('rejects missing v3 continuity, future evidence, invalid questions and foreign fields on old modes', () => {
    const missing = summary(); delete missing.actions!.state.continuity;
    expect(validActionSummary(missing)).toBe(false);
    const future = summary(); future.actions!.state.continuity!.activeInquiry!.history[0].appliedStep = 5;
    expect(validActionSummary(future)).toBe(false);
    const long = summary(); long.actions!.state.continuity!.activeInquiry!.question = 'é'.repeat(257);
    expect(validActionSummary(long)).toBe(false);
    expect(validInquiryDecision({ ...inquiry, request: { kind: 'open', source: 'journal', question: 'line\nbreak' } })).toBe(false);
    const legacy = summary(); legacy.config = withAuthoredActionMode(config, 'authored-v2');
    expect(validActionSummary(legacy)).toBe(false);
    const malformed = summary(); malformed.actions!.state.continuity!.journalWindow[0].bodySha256 = 'invalid';
    expect(validActionSummary(malformed)).toBe(false);
  });

  it('rejects contradictory inquiry identities and history from its own application step', () => {
    const changed = summary(); changed.actions!.state.continuity!.activeInquiry!.id = 'different';
    expect(validActionSummary(changed)).toBe(false);
    const sameStep = summary(); sameStep.actions!.state.continuity!.activeInquiry!.history[0].appliedStep = 4;
    expect(validActionSummary(sameStep)).toBe(false);
    expect(validInquiryReceipt({ ...inquiryReceipt, status: 'rejected', rejection: 'Cannot reject a valid OPEN' }, 4)).toBe(false);
    expect(validInquiryReceipt({ ...inquiryReceipt, status: 'continued', decision: { rawDirective: 'INQUIRY: CONTINUE', request: { kind: 'continue' }, rejection: null } }, 4)).toBe(false);
    expect(validInquiryReceipt({ ...inquiryReceipt, status: 'closed', previousInquiryId: 'inquiry-4', decision: { rawDirective: 'INQUIRY: CLOSE', request: { kind: 'close' }, rejection: null } }, 4)).toBe(false);
    const rejected = { ...inquiryReceipt, status: 'rejected', previousInquiryId: 'inquiry-4', rejection: 'Invalid inquiry', decision: { rawDirective: 'INQUIRY: UNKNOWN', request: null, rejection: 'Invalid inquiry' } };
    expect(validInquiryReceipt(rejected, 4)).toBe(true);
    expect(validInquiryReceipt({ ...rejected, inquiryId: 'changed-by-rejection' }, 4)).toBe(false);
  });
});

describe('bounded input probe and inquiry evidence', () => {
  it('validates probe dimensions, norm and the recorded paired response', () => {
    expect(validProbeVector(Array<number>(48).fill(0))).toBe(true);
    expect(validProbeVector([1, 1, 1, 1, ...Array<number>(44).fill(0)])).toBe(true);
    for (const invalid of [Array<number>(47).fill(0), Array<number>(48).fill(1), [1.1, ...Array<number>(47).fill(0)], [NaN, ...Array<number>(47).fill(0)]]) expect(validProbeVector(invalid)).toBe(false);
    const mismatch = structuredClone(summary()); mismatch.actions!.state.latestReceipt!.probe!.appliedVector[0] = .4;
    expect(validActionSummary(mismatch)).toBe(false);
    const delta = structuredClone(summary()); delta.actions!.state.latestReceipt!.probe!.stateDeltaVector[0] = .2;
    expect(validActionSummary(delta)).toBe(false);
    const html = renderToStaticMarkup(<ActionReceiptView receipt={receipt} detailed/>);
    expect(html).toContain('Input probe · one step through the numerical input channel');
    expect(html).toContain('Requested input · 48 coordinates');
    expect(html).toContain('Applied input · 48 coordinates');
    expect(html).toContain('paired response below describes only the immediate recurrent state');
    expect(html).toContain('Text input withheld at step 4');
  });

  it('keeps raw inquiry commands in evidence and separates them from saved prose', () => {
    const saved: SustainedJournal = { ...journal(), promptVersion: CONTINUITY_JOURNAL_PROMPT, action: decision, actionReceipt: receipt, bodySha256: 'b'.repeat(64) };
    expect(validJournalAction(saved, config)).toBe(true);
    const html = renderToStaticMarkup(<JournalActionDetails journal={saved}/>);
    expect(html).toContain('Exact inquiry directive');
    expect(html).toContain('Inquiry opened at step 4');
    const wrong = structuredClone(saved); wrong.actionReceipt!.inquiry!.decision.request = { kind: 'close' };
    expect(validJournalAction(wrong, config)).toBe(false);
    const checkIn: SustainedJournal = { ...journal(), promptVersion: CONTINUITY_JOURNAL_PROMPT, text: 'INQUIRY: CLOSE\nNEXT: NONE', checkIn: { ordinal: 1, scheduledSeconds: 60, admittedElapsedMillis: 60000, settingsRevision: 0, prompt: 'Hello', includeTelemetry: false } };
    expect(validJournalAction(checkIn, config)).toBe(true);
    expect(renderToStaticMarkup(<JournalActionDetails journal={checkIn}/>)).toBe('');
  });

  it('shows only the supplied memory prefix while retaining separate complete response evidence', () => {
    const prefix = 'a'.repeat(2047), body = `${prefix}é a suffix outside this slot`;
    const saved: SustainedJournal = { ...journal(), promptVersion: CONTINUITY_JOURNAL_PROMPT, action: decision, actionReceipt: receipt, bodySha256: 'b'.repeat(64), memory: {
      entryId: 'older', text: `${body}\nNEXT: NONE`, sha256: 'a'.repeat(64), suppliedText: prefix, suppliedTextSha256: 'b'.repeat(64), suppliedTextTruncated: true, fullBodySha256: 'c'.repeat(64), fullBodyBytes: new TextEncoder().encode(body).length,
    } };
    expect(validJournalAction(saved, config)).toBe(true);
    const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={saved} revision="9" config={config}/>);
    const supplied = html.match(/aria-label="Previous journal text">(.*?)<\/pre>/)?.[1];
    expect(supplied).toBe(prefix);
    expect(supplied).not.toContain('suffix outside');
    expect(html).toContain('Only the bounded prefix above was supplied in this earlier-writing slot');
    expect(html).toContain('Supplied prefix SHA-256');
    expect(html).toContain('Complete body ·');
    expect(html).toContain('é a suffix outside this slot');
    const missing = structuredClone(saved); delete missing.memory!.suppliedTextTruncated;
    expect(validJournalAction(missing, config)).toBe(false);
    const oversized = structuredClone(saved); oversized.memory!.suppliedText = body;
    expect(validJournalAction(oversized, config)).toBe(false);
  });
});
