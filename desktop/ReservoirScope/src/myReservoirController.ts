import { errorText } from './api';
import { myReservoirApi } from './myReservoirApi';
import { effectivePromptVersion, effectiveOutputTokens, effectiveRequestDeadline, isSustainedPromptVersion, validWritingLimits } from './myReservoirTypes';
import type { SessionFrame } from './freshTypes';
import type { MyReservoirApi, SustainedAction, SustainedConfig, SustainedJournal, SustainedJournalPage, SustainedSummary, SustainedUpdate, SustainedBundleReport, SustainedRecoveryPage, SustainedRecoveryDetail } from './myReservoirTypes';

export interface MyReservoirState {
  summary: SustainedSummary | null; frame: SessionFrame | null; connected: boolean; busy: string | null;
  error: string; message: string; closeRequested: boolean;
  page: SustainedJournalPage | null; journal: SustainedJournal | null; journalRevision: string | null;
  readingPage: boolean; readingJournal: boolean; journalError: string; followLatest: boolean; seenJournalCount: number;
  exported: SustainedBundleReport | null; exportRevision: string | null;
  recovery: SustainedRecoveryPage | null; recovered: SustainedRecoveryDetail | null; recoveryBusy: boolean; recoveryError: string; recoveryMessage: string;
}
const empty = (): MyReservoirState => ({ summary: null, frame: null, connected: false, busy: null, error: '', message: '', closeRequested: false, page: null, journal: null, journalRevision: null, readingPage: false, readingJournal: false, journalError: '', followLatest: true, seenJournalCount: 0, exported: null, exportRevision: null, recovery: null, recovered: null, recoveryBusy: false, recoveryError: '', recoveryMessage: '' });
const ordinal = (value: string) => typeof value === 'string' && /^[0-9]{1,20}$/.test(value);
const snapshotOrdinal = (value: string) => typeof value === 'string' && /^[1-9][0-9]{0,19}$/.test(value) && BigInt(value) <= 18446744073709551615n;
const bounded = (value: number, maximum = 1_000_000) => Number.isSafeInteger(value) && value >= 0 && value <= maximum;
const finite = (values: number[] | null, size?: number) => Array.isArray(values) && (size === undefined || values.length === size) && values.every(Number.isFinite);
function check(update: SustainedUpdate) {
  const s = update.summary, f = update.frame;
  if (typeof update.closeRequested !== 'boolean' || !update.requestId) throw new Error('The session update has no valid request identity.');
  if (!snapshotOrdinal(update.snapshotSequence)) throw new Error('The session update has no canonical snapshot sequence.');
  if (!s) { if (f) throw new Error('A state frame has no owning session.'); return; }
  if (!s.config || !isSustainedPromptVersion(effectivePromptVersion(s.config))) throw new Error('The session has an unsupported journal prompt version.');
  if (!validWritingLimits(s.config)) throw new Error('The session has invalid retained writing limits.');
  if (!s.sessionId || !ordinal(s.generation) || !ordinal(s.revision) || !bounded(s.step) || !bounded(s.durableStep) || s.durableStep > s.step || !bounded(s.journalCount, 10000) || !bounded(s.turnCount, 10000) || s.journalCount > s.turnCount || !bounded(s.usedBytes, Number.MAX_SAFE_INTEGER) || ![s.simulatedTime, s.elapsedSeconds].every(value => Number.isFinite(value) && value >= 0) || !Array.isArray(s.diagnostics)) throw new Error('The sustained session update has invalid identity or bounded measurements.');
  if (f && (f.step !== String(s.step) || !finite(f.state, 32) || !finite(f.input, 66) || !finite(f.noise, 32) || f.eigenvalues !== null && !finite(f.eigenvalues, 32) || f.fillPercent !== null && (!Number.isFinite(f.fillPercent) || f.fillPercent < 0 || f.fillPercent > 100) || f.time !== null && !Number.isFinite(f.time))) throw new Error('The current state does not match the session clock and exact vector sizes.');
}
function same(s: SustainedSummary | null, other: { sessionId: string; generation: string }) { return !!s && s.sessionId === other.sessionId && s.generation === other.generation; }
function validRow(row: { entryId: string; turnId: number; attemptId: number; observedStep: number; firstAppliedStep: number | null; status: string; sha256: string }) {
  return !!row.entryId && bounded(row.turnId, 10000) && bounded(row.attemptId, 10000) && bounded(row.observedStep) && (row.firstAppliedStep === null || bounded(row.firstAppliedStep) && row.firstAppliedStep > row.observedStep) && ['savedPendingApplication', 'applied', 'skipped'].includes(row.status) && /^[a-f0-9]{64}$/.test(row.sha256) && (row.status === 'applied') === (row.firstAppliedStep !== null);
}

/** The backend alone advances time. UI subscriptions and journal reading never start or pause it. */
export class MyReservoirController {
  private state = empty(); private listeners = new Set<() => void>();
  private serial = 0; private identityEpoch = 0; private channelEpoch = 0; private connectEpoch = 0; private pageEpoch = 0; private journalEpoch = 0;
  private recoveryEpoch = 0;
  // Process-local IPC order; never a persisted revision or numerical clock.
  private snapshotSequence = 0n;
  private active = false; private selectedId: string | null = null; private lastApplicationRead = '';
  private followRefreshNeeded = false;
  constructor(private api: MyReservoirApi = myReservoirApi) {}
  snapshot = () => this.state;
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  private set(patch: Partial<MyReservoirState>) { this.state = { ...this.state, ...patch }; this.listeners.forEach(fn => fn()); }
  private id() { return `personal-${++this.serial}`; }
  setActive(active: boolean) { const entered = active && !this.active; this.active = active; if (entered && this.state.summary?.journalCount && this.state.followLatest) void this.journals(0, true); }
  private accept(update: SustainedUpdate, replacement = false) {
    check(update); const summary = update.summary, sequence = BigInt(update.snapshotSequence);
    if (sequence <= this.snapshotSequence) return false;
    if (!summary) {
      if (this.state.summary) return false;
      this.snapshotSequence = sequence;
      this.set({ connected: true, closeRequested: update.closeRequested }); return true;
    }
    const existing = this.state.summary, matched = same(existing, summary);
    if (!replacement && !matched || matched && BigInt(summary.revision) < BigInt(existing!.revision)) return false;
    if (matched && effectivePromptVersion(summary.config) !== effectivePromptVersion(existing!.config)) throw new Error('The session changed its retained journal prompt version.');
    if (matched && (effectiveOutputTokens(summary.config) !== effectiveOutputTokens(existing!.config)
      || effectiveRequestDeadline(summary.config) !== effectiveRequestDeadline(existing!.config)
      || (summary.config.language.contextTokens ?? null) !== (existing!.config.language.contextTokens ?? null))) throw new Error('The session changed its retained writing limits.');
    this.snapshotSequence = sequence;
    const changed = !matched, grew = summary.journalCount > (existing?.journalCount ?? 0);
    if (changed) { this.identityEpoch++; this.pageEpoch++; this.journalEpoch++; this.selectedId = null; this.lastApplicationRead = ''; }
    // Numerical frames are immutable within an owning generation and step.
    // Watchdog/status updates must not re-upload unchanged GPU buffers. Null is
    // still authoritative (for example on recovery); it never revives old data.
    const priorFrame = this.state.frame;
    const frame = matched && update.frame && priorFrame?.step === update.frame.step ? priorFrame : update.frame;
    this.set({ summary, frame, connected: true, closeRequested: update.closeRequested,
      ...(changed ? { busy: null, page: null, journal: null, journalRevision: null, readingPage: false, readingJournal: false, journalError: '', followLatest: true, seenJournalCount: 0, exported: null, exportRevision: null } : {}) });
    if (!this.active) return true;
    if ((changed || grew) && summary.journalCount && this.state.followLatest) {
      if (this.state.readingPage) this.followRefreshNeeded = true;
      else void this.journals(0, true);
    }
    const j = this.state.journal, refresh = j && j.status === 'savedPendingApplication' && summary.step > j.observedStep ? `${summary.sessionId}:${j.entryId}:${summary.step}` : '';
    if (refresh && refresh !== this.lastApplicationRead && !this.state.readingJournal) { this.lastApplicationRead = refresh; void this.readJournal(j!.entryId); }
    return true;
  }
  async connect() {
    const epoch = ++this.connectEpoch, channel = ++this.channelEpoch, identity = this.identityEpoch, requestId = this.id();
    let attached = false; const queued: SustainedUpdate[] = [];
    const receive = (update: SustainedUpdate) => { if (channel !== this.channelEpoch || update.requestId !== requestId) return; if (!attached) { queued.splice(0, queued.length, update); return; } try { this.accept(update); } catch (error) { this.set({ error: errorText(error) }); } };
    try {
      const result = await this.api.get(requestId, receive);
      if (epoch !== this.connectEpoch || channel !== this.channelEpoch || identity !== this.identityEpoch) return;
      if (result.requestId !== requestId) throw new Error('Session attachment did not match this request.');
      this.accept(result, true); attached = true;
      for (const update of queued) this.accept(update);
    } catch (error) { if (epoch === this.connectEpoch && channel === this.channelEpoch) this.set({ error: errorText(error) }); }
  }
  async create(config: SustainedConfig) {
    if (this.state.busy) return false;
    if (!isSustainedPromptVersion(effectivePromptVersion(config))) { this.set({ error: 'The selected journal prompt version is unsupported.' }); return false; }
    if (!validWritingLimits(config)) { this.set({ error: 'Review the writing limits before creating a session.' }); return false; }
    const identity = this.identityEpoch, requestId = this.id(), prior = this.state.summary;
    this.set({ busy: 'create', error: '', message: '' }); let accepted = false;
    try {
      const result = await this.api.create(requestId, config);
      if (identity !== this.identityEpoch) return false;
      if (result.requestId !== requestId || !result.summary || same(prior, result.summary)) throw new Error('Creation did not return a new session identity.');
      if (!this.accept(result, true)) throw new Error('A newer session snapshot superseded this replacement.');
      this.channelEpoch++; accepted = true;
      this.set({ message: 'Your session is prepared locally. Start explicitly when ready.' }); return true;
    } catch (error) { if (identity === this.identityEpoch) this.set({ error: errorText(error) }); return false; }
    finally { this.set({ busy: null }); if (accepted) void this.connect(); }
  }
  async action(action: SustainedAction) {
    const summary = this.state.summary; if (!summary || this.state.busy) return false;
    const available = { start: summary.canStart, pause: summary.canPause, stop: summary.canStop, retrySave: summary.canRetrySave, retryProvider: summary.canRetryProvider, skipFeedback: summary.canSkipFeedback };
    if (!available[action]) { this.set({ error: 'This action is not available at the current backend boundary.' }); return false; }
    const epoch = this.identityEpoch, requestId = this.id(); this.set({ busy: action, error: '', message: '' });
    try {
      const result = await this.api.action(action, requestId, summary.sessionId, summary.generation, summary.pendingApplication?.entryId ?? summary.pendingSave?.entryId ?? null, summary.pendingApplication?.attemptId ?? summary.pendingSave?.attemptId ?? summary.pendingLanguage?.attemptId ?? null);
      if (epoch !== this.identityEpoch) return false;
      if (result.requestId !== requestId || !result.summary || !same(summary, result.summary)) throw new Error('The action result did not match this session generation.');
      this.accept(result); return true;
    } catch (error) { if (epoch === this.identityEpoch) this.set({ error: errorText(error) }); return false; }
    finally { if (epoch === this.identityEpoch) this.set({ busy: null }); }
  }
  async journals(offset = 0, follow = false) {
    const summary = this.state.summary; if (!summary || !bounded(offset, 10000)) return;
    const epoch = ++this.pageEpoch, identity = this.identityEpoch, requestId = this.id();
    let accepted = false; this.followRefreshNeeded = false;
    if (!follow) this.set({ followLatest: false, seenJournalCount: summary.journalCount });
    this.set({ readingPage: true, journalError: '' });
    try {
      const result = await this.api.journals(requestId, summary.sessionId, summary.generation, offset, 20);
      if (epoch !== this.pageEpoch || identity !== this.identityEpoch) return;
      if (result.requestId !== requestId || !same(summary, result) || !ordinal(result.revision) || result.offset !== offset || !bounded(result.total, 10000) || result.entries.length > 20 || new Set(result.entries.map(e => e.entryId)).size !== result.entries.length || result.entries.some(row => !validRow(row))) throw new Error('Journal page did not match the selected session and bounded request.');
      this.set({ page: result }); accepted = true;
      if (follow && this.state.followLatest) {
        this.set({ seenJournalCount: result.total });
        const latest = result.entries[0]; if (latest && (this.selectedId !== latest.entryId || this.state.journal?.status !== latest.status)) void this.readJournal(latest.entryId);
      }
    } catch (error) { if (epoch === this.pageEpoch && identity === this.identityEpoch) this.set({ journalError: errorText(error) }); }
    finally { if (epoch === this.pageEpoch && identity === this.identityEpoch) { this.set({ readingPage: false }); const refresh = this.followRefreshNeeded; this.followRefreshNeeded = false; if (accepted && refresh && this.active && this.state.followLatest) void this.journals(0, true); } }
  }
  selectJournal(entryId: string) { this.pageEpoch++; this.followRefreshNeeded = false; this.set({ followLatest: false, readingPage: false, seenJournalCount: this.state.summary?.journalCount ?? 0 }); return this.readJournal(entryId); }
  private async readJournal(entryId: string) {
    const summary = this.state.summary; if (!summary) return;
    const epoch = ++this.journalEpoch, identity = this.identityEpoch, requestId = this.id(); this.selectedId = entryId;
    this.set({ readingJournal: true, journalError: '' });
    try {
      const result = await this.api.journal(requestId, summary.sessionId, summary.generation, entryId);
      if (epoch !== this.journalEpoch || identity !== this.identityEpoch || this.selectedId !== entryId) return;
      const j = result.journal;
      if (result.requestId !== requestId || !same(summary, result) || !ordinal(result.revision) || j.entryId !== entryId || !isSustainedPromptVersion(j.promptVersion) || j.promptVersion !== effectivePromptVersion(summary.config) || !validRow(j) || !finite(j.encodedFeatures) || !finite(j.semanticVector) || j.saveReceipt.entryId !== entryId || j.saveReceipt.sha256 !== j.sha256) throw new Error('Journal detail did not match its identity and saved evidence.');
      this.set({ journal: j, journalRevision: result.revision });
    } catch (error) { if (epoch === this.journalEpoch && identity === this.identityEpoch) this.set({ journalError: errorText(error) }); }
    finally { if (epoch === this.journalEpoch && identity === this.identityEpoch) this.set({ readingJournal: false }); }
  }
  followLatest() { this.set({ followLatest: true, seenJournalCount: this.state.summary?.journalCount ?? 0 }); return this.journals(0, true); }
  refreshJournal() { if (this.state.journal) return this.readJournal(this.state.journal.entryId); }
  async export() {
    const s = this.state.summary; if (!s || this.state.busy) return;
    const epoch = this.identityEpoch, requestId = this.id(); this.set({ busy: 'export', error: '', message: '' });
    try {
      const result = await this.api.export(requestId, s.sessionId, s.generation, s.revision);
      if (epoch !== this.identityEpoch) return;
      if (result.requestId !== requestId || !same(s, result) || result.revision !== s.revision || result.bundle && !validReport(result.bundle, s.sessionId)) throw new Error('Export did not match the selected session snapshot.');
      this.set(result.bundle ? { exported: result.bundle, exportRevision: result.revision, message: 'Committed session exported into a new immutable bundle directory.' } : { message: 'Export cancelled. The session and selected journal remain available.' });
    } catch (error) { if (epoch === this.identityEpoch) this.set({ error: errorText(error) }); }
    finally { if (epoch === this.identityEpoch) this.set({ busy: null }); }
  }
  async recovery() {
    const epoch = ++this.recoveryEpoch, requestId = this.id(); this.set({ recoveryBusy: true, recoveryError: '', recoveryMessage: '' });
    try {
      const result = await this.api.recovery(requestId);
      if (epoch !== this.recoveryEpoch) return;
      if (result.requestId !== requestId || !Array.isArray(result.entries) || result.entries.length > 1000 || typeof result.complete !== 'boolean') throw new Error('Recovery catalog did not match the bounded request.');
      this.set({ recovery: result });
    } catch (error) { if (epoch === this.recoveryEpoch) this.set({ recoveryError: errorText(error) }); }
    finally { if (epoch === this.recoveryEpoch) this.set({ recoveryBusy: false }); }
  }
  async inspect(sessionId: string) {
    const epoch = ++this.recoveryEpoch, requestId = this.id(); this.set({ recoveryBusy: true, recoveryError: '', recoveryMessage: '' });
    try {
      const result = await this.api.inspect(requestId, sessionId);
      if (epoch !== this.recoveryEpoch) return;
      if (result.requestId !== requestId || result.manifest.sessionId !== sessionId || !ordinal(result.manifest.generation) || !ordinal(result.manifest.revision) || !validReport(result.report, sessionId) || result.manifest.checkpointSha256 !== result.report.checkpointSha256 || result.manifest.step !== result.report.step) throw new Error('Recovery inspection did not match the selected session and checkpoint.');
      this.set({ recovered: result });
    } catch (error) { if (epoch === this.recoveryEpoch) this.set({ recoveryError: errorText(error) }); }
    finally { if (epoch === this.recoveryEpoch) this.set({ recoveryBusy: false }); }
  }
  async restore() {
    const recovered = this.state.recovered; if (!recovered || this.state.busy || this.state.recoveryBusy) return;
    const m = recovered.manifest, epoch = ++this.recoveryEpoch, identity = this.identityEpoch, requestId = this.id(); let accepted = false;
    this.set({ busy: 'restore', recoveryBusy: true, recoveryError: '', recoveryMessage: '' });
    try {
      const result = await this.api.restore(requestId, m.sessionId, m.generation, m.revision);
      if (epoch !== this.recoveryEpoch || identity !== this.identityEpoch) return;
      if (result.requestId !== requestId || !result.summary || result.summary.sessionId !== m.sessionId || result.summary.generation === m.generation || ['running', 'awaitingLanguage', 'savingJournal'].includes(result.summary.phase)) throw new Error('Recovery did not restore this session into a new held generation.');
      if (effectivePromptVersion(result.summary.config) !== effectivePromptVersion(m.config)) throw new Error('Recovery changed the inspected journal prompt version.');
      if (!this.accept(result, true)) throw new Error('A newer session snapshot superseded this replacement.');
      this.channelEpoch++; accepted = true; this.set({ recoveryMessage: 'Verified continuation restored without starting execution. Review its boundary, then Start explicitly.' });
    } catch (error) { if (epoch === this.recoveryEpoch) this.set({ recoveryError: errorText(error) }); }
    finally { if (epoch === this.recoveryEpoch) this.set({ busy: null, recoveryBusy: false }); if (accepted) void this.connect(); }
  }
  async exportRecovery() {
    const recovered = this.state.recovered; if (!recovered || this.state.recoveryBusy || this.state.busy) return;
    const m = recovered.manifest, epoch = ++this.recoveryEpoch, requestId = this.id(); this.set({ recoveryBusy: true, recoveryError: '', recoveryMessage: '' });
    try {
      const result = await this.api.export(requestId, m.sessionId, m.generation, m.revision);
      if (epoch !== this.recoveryEpoch) return;
      if (result.requestId !== requestId || result.sessionId !== m.sessionId || result.generation !== m.generation || result.revision !== m.revision || result.bundle && (!validReport(result.bundle, m.sessionId) || result.bundle.manifestSha256 !== recovered.report.manifestSha256)) throw new Error('Recovery export did not match the inspected immutable snapshot.');
      this.set({ recoveryMessage: result.bundle ? `Committed history through step ${result.bundle.step} exported · manifest SHA-256 ${result.bundle.manifestSha256}. Unsaved work is not included.` : 'Recovery export cancelled. The inspected session remains selected.' });
    } catch (error) { if (epoch === this.recoveryEpoch) this.set({ recoveryError: errorText(error) }); }
    finally { if (epoch === this.recoveryEpoch) this.set({ recoveryBusy: false }); }
  }
  async listenClose() { const stop = await this.api.listenClose(() => { this.set({ closeRequested: true }); void this.connect(); }); await this.connect(); return stop; }
  async returnToApp() {
    try {
      await this.api.cancelClose(); this.set({ closeRequested: false, error: '' });
      // Replace the old channel and obtain a post-cancellation sequence so an
      // in-flight closeRequested snapshot cannot reopen the dismissed review.
      await this.connect();
    } catch (error) { this.set({ error: errorText(error) }); }
  }
  async finishClose(allowDiscard: boolean) {
    if (this.state.busy) return;
    this.set({ busy: 'close', error: '' });
    try { if (!await this.api.finishClose(allowDiscard)) this.set({ error: 'The backend still requires a persistence or close decision. Retained evidence remains available.' }); }
    catch (error) { this.set({ error: errorText(error) }); }
    finally { this.set({ busy: null }); }
  }
}
function validReport(report: SustainedBundleReport, sessionId: string) { return report.sessionId === sessionId && /^[a-f0-9]{64}$/.test(report.manifestSha256) && /^[a-f0-9]{64}$/.test(report.checkpointSha256) && bounded(report.step) && bounded(report.journalCount, 10000) && bounded(report.sizeBytes, Number.MAX_SAFE_INTEGER) && typeof report.verification === 'string'; }
export const myReservoirController = new MyReservoirController();
