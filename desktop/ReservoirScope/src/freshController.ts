import { errorText } from './api';
import { freshApi } from './freshApi';
import type { FileProof } from './types';
import type { ExplorationControls, FreshAction, FreshApi, PendingJournalView, RecoveryCheckpoint, RecoveryPage, SessionConfig, SessionFrame, SessionFrames, SessionSummary, SessionTrackId, SessionTurn, SessionUpdate, RegulationFrames, RegulationDetails } from './freshTypes';

export interface FreshState {
  summary: SessionSummary | null; frame: SessionFrame | null; latestFrame: SessionFrame | null; frames: SessionFrames | null; latestFrames: SessionFrames | null; selectedTrack: SessionTrackId; pendingJournal: PendingJournalView | null;
  regulationFrames: RegulationFrames | null; latestRegulationFrames: RegulationFrames | null; regulationDetails: RegulationDetails | null; readingRegulationDetails: boolean;
  turn: SessionTurn | null; turnRevision: string | null; node: number; followLatest: boolean;
  busy: string | null; readingFrame: boolean; readingTurn: boolean; connected: boolean; closeRequested: boolean;
  error: string; message: string; exported: FileProof | null; exportRevision: string | null;
  recovery: RecoveryPage | null; recovered: RecoveryCheckpoint | null; recoveryBusy: boolean; recoveryError: string; recoveryMessage: string;
}
const empty = (): FreshState => ({ summary: null, frame: null, latestFrame: null, frames: null, latestFrames: null, selectedTrack: 'right', regulationFrames: null, latestRegulationFrames: null, regulationDetails: null, readingRegulationDetails: false, pendingJournal: null, turn: null, turnRevision: null, node: 0, followLatest: true, busy: null, readingFrame: false, readingTurn: false, connected: false, closeRequested: false, error: '', message: '', exported: null, exportRevision: null, recovery: null, recovered: null, recoveryBusy: false, recoveryError: '', recoveryMessage: '' });
const ordinal = (value: string) => /^[0-9]{1,20}$/.test(value);
const integer = (value: number, maximum = 3000) => Number.isInteger(value) && value >= 0 && value <= maximum;
function checkSummary(summary: SessionSummary) {
  if (!summary.sessionId || !ordinal(summary.generation) || !ordinal(summary.revision) || !integer(summary.step) || !integer(summary.durableStep) || summary.durableStep > summary.step || !integer(summary.stepLimit) || summary.stepLimit < 1 || summary.step > summary.stepLimit || !integer(summary.frameCount) || !integer(summary.turnCount, 3000) || !integer(summary.journalCount, 256) || typeof summary.pendingWrites !== 'boolean') throw new Error('The backend session summary has invalid identity or finite bounds.');
  if (summary.config.recipe === 'regulation' && (!summary.regulationSpec || summary.stepLimit !== 600 || summary.regulationSpec.steps !== 600 || summary.regulationSpec.targetFillPercent !== 68 || summary.regulationSpec.evaluationFirstStep !== 301 || summary.regulationSpec.evaluationLastStep !== 600 || summary.tracks.length !== 2 || summary.turnCount !== 0 || summary.journalCount !== 0 || summary.action !== null || summary.canRequestJournal || (summary.step < 600 && summary.canExport))) throw new Error('The field-only study summary violates its fixed 600-step contract.');
  const pending = summary.pendingLanguage;
  if (pending && (!pending.operationId || !['left', 'right'].includes(pending.arm) || !summary.tracks.some(track => track.id === pending.arm) || !integer(pending.turnId) || pending.turnId < 1 || !integer(pending.observedStep) || pending.observedStep > summary.step || !pending.endpoint || !pending.model || !['prepared', 'requesting', 'compatibilityBlocked'].includes(pending.state) || summary.config.language?.backend !== 'ollama' || summary.canExport || summary.canStep || summary.canRun || summary.canRequestJournal)) throw new Error('Pending language metadata does not match a held local-model boundary.');
  if (summary.phase === 'awaitingLanguage' && !pending) throw new Error('The held language phase has no request identity.');
  if (!Array.isArray(summary.tracks) || summary.tracks.length < 1 || summary.tracks.length > 2 || !summary.tracks.some(track => track.id === 'right') || new Set(summary.tracks.map(track => track.id)).size !== summary.tracks.length || summary.tracks.some(track => !['left', 'right'].includes(track.id) || track.frameCount !== summary.frameCount || !integer(track.turnCount, 3000) || !integer(track.journalCount, 128))) throw new Error('The backend tracks do not share a bounded retained frame clock.');
}
function checkFrame(frame: SessionFrame, count: number) {
  if (!integer(frame.index) || frame.index >= count || !ordinal(frame.step) || frame.state.length !== 32 || frame.state.some(v => !Number.isFinite(v)) || !Array.isArray(frame.input) || frame.input.some(v => !Number.isFinite(v)) || !Array.isArray(frame.noise) || frame.noise.some(v => !Number.isFinite(v)) || (frame.time !== null && !Number.isFinite(frame.time)) || (frame.fillPercent !== null && !Number.isFinite(frame.fillPercent)) || (frame.eigenvalues !== null && frame.eigenvalues.some(v => !Number.isFinite(v)))) throw new Error('The backend frame does not contain a bounded, finite 32-node observation.');
  if ((frame.retentionUsed !== null && (!Number.isFinite(frame.retentionUsed) || frame.retentionUsed < 0 || frame.retentionUsed > 1)) || (frame.nextRetention != null && !Number.isFinite(frame.nextRetention)) || (frame.control !== null && [frame.control.error, frame.control.integral, frame.control.requestedRetention, frame.control.appliedRetention].some(value => !Number.isFinite(value)))) throw new Error('The backend frame has a nonfinite retention or controller measurement.');
}

function checkFrames(frames: SessionFrames, summary: SessionSummary) {
  checkFrame(frames.right, summary.frameCount);
  const paired = summary.tracks.some(track => track.id === 'left');
  if (paired !== (frames.left !== null)) throw new Error('The frame pair does not match the accepted tracks.');
  if (frames.left) {
    checkFrame(frames.left, summary.frameCount);
    if (frames.left.index !== frames.right.index || frames.left.step !== frames.right.step || frames.left.time !== frames.right.time) throw new Error('The retained frames are not on the same numerical boundary.');
  }
}

function checkRegulationFrames(frames: RegulationFrames, summary: SessionSummary) {
  for (const frame of [frames.left, frames.right]) {
    if (!frame || !integer(frame.index, 599) || frame.index >= summary.frameCount || frame.step !== String(frame.index + 1) || !Number.isFinite(frame.time)
      || ![frame.input, frame.fieldVector, frame.eigenvalues].every((values, i) => Array.isArray(values) && values.length === (i === 0 ? 66 : 32) && values.every(Number.isFinite))
      || !Number.isFinite(frame.fillPercent) || frame.fillPercent < 0 || frame.fillPercent > 100 || (!Number.isFinite(frame.retentionUsed) || frame.retentionUsed < 0 || frame.retentionUsed > 1)
      || (frame.nextRetention !== null && !Number.isFinite(frame.nextRetention))
      || (frame.control !== null && Object.values(frame.control).some(value => !Number.isFinite(value)))) throw new Error('The field-only frame does not contain bounded finite measurements.');
    const step = frame.index + 1, evidence = frame.regulationEvidence;
    if (step <= 300 ? evidence !== null : !evidence || evidence.firstStep !== 301 || evidence.lastStep !== step || evidence.count !== step - 300 || evidence.isComplete !== (step === 600) || ![evidence.baselineMeanAbsoluteError, evidence.regulatedMeanAbsoluteError].every(value => Number.isFinite(value) && value >= 0)) throw new Error('Controller evidence does not match the reached evaluation prefix.');
  }
  if (frames.left.index !== frames.right.index || frames.left.step !== frames.right.step || frames.left.time !== frames.right.time || frames.left.input.some((value, index) => value !== frames.right.input[index]) || JSON.stringify(frames.left.regulationEvidence) !== JSON.stringify(frames.right.regulationEvidence)) throw new Error('The field-only pair does not share one numerical boundary and input.');
}

/** One backend-owned session survives navigation. There is no frontend numerical clock. */
export class FreshController {
  private state = empty(); private listeners = new Set<() => void>();
  private serial = 0; private identityEpoch = 0; private channelEpoch = 0; private readEpoch = 0; private turnEpoch = 0;
  private connectSerial = 0;
  private recoveryEpoch = 0; private detailsEpoch = 0;
  constructor(private api: FreshApi = freshApi) {}
  snapshot = () => this.state;
  subscribe = (fn: () => void) => { this.listeners.add(fn); return () => { this.listeners.delete(fn); }; };
  private set(patch: Partial<FreshState>) { this.state = { ...this.state, ...patch }; this.listeners.forEach(fn => fn()); }
  private id() { return `fresh-${++this.serial}`; }
  private same(summary: SessionSummary) { return this.state.summary?.sessionId === summary.sessionId && this.state.summary.generation === summary.generation; }
  private accept(update: SessionUpdate, replacement = false) {
    const summary = update.summary;
    if (!summary) {
      if (replacement && !this.state.summary) this.set({ connected: true, closeRequested: update.closeRequested });
      return;
    }
    checkSummary(summary);
    if (this.same(summary) && BigInt(summary.revision) < BigInt(this.state.summary!.revision)) return;
    if (!replacement && !this.same(summary)) return;
    const fieldOnly = summary.config.recipe === 'regulation';
    if (fieldOnly) {
      if (update.frame || update.frames || update.pendingJournal || (summary.frameCount > 0 && !update.regulationFrames)) throw new Error('Field-only study supplied a reservoir frame or omitted its field pair.');
      if (update.regulationFrames) checkRegulationFrames(update.regulationFrames, summary);
    } else {
      if (update.regulationFrames) throw new Error('A reservoir recipe returned field-only study measurements.');
      if (update.frames) checkFrames(update.frames, summary);
    }
    const changed = !this.same(summary);
    if (changed) { this.identityEpoch++; this.readEpoch++; this.turnEpoch++; this.detailsEpoch++; }
    const selectedTrack = changed ? 'right' : this.state.selectedTrack;
    const latestFrames = fieldOnly ? null : update.frames ?? (changed ? null : this.state.latestFrames);
    const latestRegulationFrames = fieldOnly ? update.regulationFrames ?? null : null;
    const regulationFrames = changed || this.state.followLatest ? latestRegulationFrames : this.state.regulationFrames;
    const frames = changed || this.state.followLatest ? latestFrames : this.state.frames;
    const latestFrame = latestFrames?.[selectedTrack] ?? null;
    const wasRunning = this.state.summary?.phase === 'running', wasAwaitingLanguage = !!this.state.summary?.pendingLanguage;
    this.set({ summary, selectedTrack, regulationFrames, latestRegulationFrames, frames, latestFrames, latestFrame, frame: frames?.[selectedTrack] ?? null, pendingJournal: update.pendingJournal, closeRequested: update.closeRequested,
      connected: true, ...(changed ? { regulationDetails: null, readingRegulationDetails: false, turn: null, turnRevision: null, node: 0, followLatest: true, exported: null, exportRevision: null, readingFrame: false, readingTurn: false } : {}) });
    if ((wasRunning && summary.phase !== 'running' || wasAwaitingLanguage && !summary.pendingLanguage) && this.state.turn && !this.state.readingTurn) void this.turn(this.state.turn.index);
  }
  private channel(requestId: string, epoch: number) {
    return (update: SessionUpdate) => {
      if (epoch !== this.channelEpoch || update.requestId !== requestId) return;
      try { this.accept(update); } catch (error) { this.set({ error: errorText(error) }); }
    };
  }
  async connect() {
    if (this.state.busy) return;
    const requestId = this.id(), serial = ++this.connectSerial, epoch = this.identityEpoch, channel = ++this.channelEpoch;
    try {
      const result = await this.api.get(requestId, this.channel(requestId, channel));
      if (serial !== this.connectSerial || epoch !== this.identityEpoch || channel !== this.channelEpoch) return;
      if (result.requestId !== requestId) throw new Error('Session attachment did not match its request.');
      this.accept(result, true); this.set({ connected: true, error: '' });
    } catch (error) { if (serial === this.connectSerial && epoch === this.identityEpoch) this.set({ error: errorText(error) }); }
  }
  async create(config: SessionConfig) {
    if (this.state.busy) return;
    const requestId = this.id(); ++this.connectSerial; let reattach = false;
    this.set({ busy: 'create', error: '', message: 'Creating a finite local session…' });
    try {
      const result = await this.api.create(requestId, config);
      if (result.requestId !== requestId || !result.summary) throw new Error('Creation returned no matching backend session.');
      if (this.state.summary && this.same(result.summary)) throw new Error('Creation did not return a new session identity. The accepted session is retained.');
      this.channelEpoch++; this.accept(result, true); reattach = true;
      this.set({ message: 'Session created. No step has run; choose Step or Run.' });
    } catch (error) { this.set({ error: errorText(error), message: 'The previous accepted session, if any, is retained.' }); }
    finally { this.set({ busy: null }); if (reattach) void this.connect(); }
  }
  async action(action: FreshAction, discard = false) {
    const summary = this.state.summary; if (!summary || this.state.busy) return false;
    if (summary.pendingLanguage && ['step', 'pulse', 'run', 'reset', 'saveRecord', 'requestJournal'].includes(action)) { this.set({ error: 'The language boundary is unresolved. Pause or explicitly cancel and stop it first.' }); return false; }
    if (action === 'saveRecord' && summary.config.recipe === 'regulation' && !summary.canExport) { this.set({ error: 'Only a complete 600-step controller study can be saved as a portable record.' }); return false; }
    const requestId = this.id(), epoch = this.identityEpoch;
    const channel = action === 'run' ? ++this.channelEpoch : this.channelEpoch; let reattach = false;
    this.set({ busy: action, error: '', message: '' });
    try {
      const candidate = action === 'saveJournal' ? this.state.pendingJournal : null;
      if (action === 'saveJournal' && !candidate) throw new Error('No pending journal candidate is selected for saving.');
      const result = await this.api.action(action, requestId, summary.sessionId, summary.generation, this.channel(requestId, channel), discard, candidate ? { arm: candidate.arm, entryId: candidate.id } : undefined);
      if (epoch !== this.identityEpoch) return false;
      if (result.requestId !== requestId || !result.summary || (action !== 'reset' && (result.summary.sessionId !== summary.sessionId || result.summary.generation !== summary.generation))) throw new Error('Session operation returned a mismatched identity.');
      if (action === 'reset' && (result.summary.sessionId === summary.sessionId || result.summary.generation === summary.generation)) throw new Error('Reset did not return a new session and generation. The accepted session is retained.');
      if (action === 'reset') { this.channelEpoch++; this.accept(result, true); reattach = true; } else this.accept(result);
      const message = action === 'saveJournal' ? 'Journal save response received. Eligibility and the next application boundary are owned by the backend.' : action === 'saveRecord' ? result.summary.unsavedRecord ? 'The record remains unsaved. Inspect the diagnostic and retry.' : 'Experiment saved to the local Library.' : action === 'reset' ? 'Reset accepted. Previous channel callbacks cannot change this new generation.' : action === 'stop' ? 'The finite session is stopped; retained evidence remains available.' : '';
      this.set({ message });
      if (this.state.turn && !this.state.readingTurn && ['step', 'pulse', 'saveJournal', 'pause'].includes(action)) void this.turn(this.state.turn.index);
      return !result.summary.saveError;
    } catch (error) { if (epoch === this.identityEpoch) this.set({ error: errorText(error), message: 'The accepted session and retained evidence remain available.' }); return false; }
    finally { this.set({ busy: null }); if (reattach) void this.connect(); }
  }
  async controls(controls: ExplorationControls) {
    const summary = this.state.summary; if (!summary || this.state.busy || summary.config.recipe !== 'exploration') return;
    const requestId = this.id(), epoch = this.identityEpoch; this.set({ busy: 'controls', error: '', message: '' });
    try {
      const result = await this.api.controls(requestId, summary.sessionId, summary.generation, controls);
      if (epoch !== this.identityEpoch) return;
      if (result.requestId !== requestId || result.summary?.sessionId !== summary.sessionId || result.summary.generation !== summary.generation) throw new Error('Control update did not match the accepted session.');
      this.accept(result); this.set({ message: 'Explore controls accepted for the next numerical boundary. Earlier frames keep their actual applied controls.' });
    } catch (error) { if (epoch === this.identityEpoch) this.set({ error: errorText(error) }); }
    finally { this.set({ busy: null }); }
  }
  node(index: number) { if (integer(index, 31)) this.set({ node: index }); }
  selectTrack(trackId: SessionTrackId) {
    if (trackId === this.state.selectedTrack || !this.state.summary?.tracks.some(track => track.id === trackId)) return;
    this.readEpoch++; this.turnEpoch++;
    this.set({ selectedTrack: trackId, frame: this.state.frames?.[trackId] ?? null, latestFrame: this.state.latestFrames?.[trackId] ?? null, turn: null, turnRevision: null, readingFrame: false, readingTurn: false });
  }
  follow() { this.readEpoch++; this.detailsEpoch++; this.set({ followLatest: true, regulationFrames: this.state.latestRegulationFrames, readingRegulationDetails: false, frames: this.state.latestFrames, frame: this.state.latestFrame, readingFrame: false }); }
  async frame(index: number) {
    const summary = this.state.summary; if (!summary || !integer(index) || index >= summary.frameCount) return;
    const epoch = this.identityEpoch, read = ++this.readEpoch; this.detailsEpoch++;
    this.set({ readingRegulationDetails: false, readingFrame: true, followLatest: false, error: '' });
    try {
      const results = await Promise.all(summary.tracks.map(async track => {
        const requestId = this.id();
        const result = await this.api.frame(requestId, summary.sessionId, summary.generation, index, track.id);
        if (result.requestId !== requestId || result.sessionId !== summary.sessionId || result.generation !== summary.generation || result.trackId !== track.id || (summary.config.recipe === 'regulation' ? result.frame !== null || result.regulationFrame?.index !== index : result.frame?.index !== index || !!result.regulationFrame)) throw new Error('Frame response did not match the requested session track and boundary.');
        return result;
      }));
      if (epoch !== this.identityEpoch || read !== this.readEpoch) return;
      if (summary.config.recipe === 'regulation') {
        const regulationFrames: RegulationFrames = { right: results.find(result => result.trackId === 'right')!.regulationFrame!, left: results.find(result => result.trackId === 'left')!.regulationFrame! };
        checkRegulationFrames(regulationFrames, this.state.summary!); this.set({ regulationFrames });
      } else {
        const frames: SessionFrames = { right: results.find(result => result.trackId === 'right')!.frame!, left: results.find(result => result.trackId === 'left')?.frame ?? null };
        checkFrames(frames, this.state.summary!); this.set({ frames, frame: frames[this.state.selectedTrack] });
      }
    } catch (error) { if (epoch === this.identityEpoch && read === this.readEpoch) this.set({ error: errorText(error) }); }
    finally { if (epoch === this.identityEpoch && read === this.readEpoch) this.set({ readingFrame: false }); }
  }
  async regulationDetails() {
    const summary = this.state.summary, cursor = this.state.regulationFrames?.right.index;
    if (!summary || summary.config.recipe !== 'regulation' || cursor === undefined || this.state.readingRegulationDetails) return;
    const requestId = this.id(), epoch = this.identityEpoch, read = ++this.detailsEpoch, cursorStep = cursor + 1;
    this.set({ readingRegulationDetails: true, error: '' });
    try {
      const result = await this.api.regulationDetails(requestId, summary.sessionId, summary.generation, cursorStep);
      if (epoch !== this.identityEpoch || read !== this.detailsEpoch || this.state.regulationFrames?.right.index !== cursor) return;
      if (result.requestId !== requestId || result.sessionId !== summary.sessionId || result.generation !== summary.generation || !ordinal(result.revision) || result.cursorStep !== cursorStep || result.projectionWeights.length !== 2112 || result.projectionWeights.some(value => !Number.isFinite(value)) || result.timeline.length !== cursorStep || result.timeline.some((point, index) => point.step !== String(index + 1) || ![point.baselineFill, point.regulatedFill, point.baselineRetention, point.regulatedRetention].every(Number.isFinite) || point.baselineFill < 0 || point.baselineFill > 100 || point.regulatedFill < 0 || point.regulatedFill > 100 || point.baselineRetention < 0 || point.baselineRetention > 1 || point.regulatedRetention < 0 || point.regulatedRetention > 1)) throw new Error('Controller detail response does not match the bounded selected prefix.');
      this.set({ regulationDetails: result });
    } catch (error) { if (epoch === this.identityEpoch && read === this.detailsEpoch) this.set({ error: errorText(error) }); }
    finally { if (epoch === this.identityEpoch && read === this.detailsEpoch) this.set({ readingRegulationDetails: false }); }
  }
  async turn(index: number) {
    const summary = this.state.summary, trackId = this.state.selectedTrack;
    const track = summary?.tracks.find(item => item.id === trackId);
    if (!summary || !track || !integer(index) || index >= track.turnCount) return;
    const requestId = this.id(), epoch = this.identityEpoch, read = ++this.turnEpoch;
    this.set({ readingTurn: true, error: '' });
    try {
      const result = await this.api.turn(requestId, summary.sessionId, summary.generation, index, trackId);
      if (epoch !== this.identityEpoch || read !== this.turnEpoch) return;
      if (result.requestId !== requestId || result.sessionId !== summary.sessionId || result.generation !== summary.generation || result.trackId !== trackId || result.turn.index !== index || !ordinal(result.revision)) throw new Error('Turn response did not match the requested session evidence.');
      this.set({ turn: result.turn, turnRevision: result.revision });
    } catch (error) { if (epoch === this.identityEpoch && read === this.turnEpoch) this.set({ error: errorText(error) }); }
    finally { if (epoch === this.identityEpoch && read === this.turnEpoch) this.set({ readingTurn: false }); }
  }
  async exportProgress() {
    const summary = this.state.summary;
    if (!summary || summary.config.recipe !== 'regulation' || summary.step >= 600 || summary.phase === 'running' || this.state.busy || summary.pendingWrites) return;
    const epoch = this.identityEpoch, requestId = this.id(); this.set({ busy: 'export-progress', error: '', message: '' });
    try {
      // Pause also publishes the latest progress metadata, including manual steps
      // since the last periodic checkpoint. Never export an older checkpoint as current.
      const pauseId = this.id();
      const paused = await this.api.action('pause', pauseId, summary.sessionId, summary.generation, this.channel(pauseId, this.channelEpoch));
      if (epoch !== this.identityEpoch) return;
      if (paused.requestId !== pauseId || paused.summary?.sessionId !== summary.sessionId || paused.summary.generation !== summary.generation) throw new Error('Progress checkpoint pause returned a different session.');
      this.accept(paused);
      if (paused.summary.phase === 'storageBlocked' || paused.summary.saveError) throw new Error(paused.summary.saveError ?? 'Progress checkpoint could not be saved.');
      const checkpoint = await this.api.recovered(summary.sessionId);
      if (epoch !== this.identityEpoch) return;
      if (checkpoint.sessionId !== summary.sessionId || checkpoint.generation !== summary.generation || !ordinal(checkpoint.revision) || checkpoint.recordSha256 !== null || checkpoint.step !== paused.summary.step || checkpoint.revision !== paused.summary.revision) throw new Error('Progress checkpoint does not match this partial field study. Refresh and inspect recovery.');
      const result = await this.api.exportRecovery(requestId, summary.sessionId, 'checkpoint', checkpoint.generation, checkpoint.revision);
      if (epoch !== this.identityEpoch) return;
      if (result.requestId !== requestId || result.sessionId !== summary.sessionId || result.generation !== checkpoint.generation || result.revision !== checkpoint.revision) throw new Error('Progress export did not match its captured checkpoint.');
      this.set({ exported: result.file ?? this.state.exported, exportRevision: result.file ? result.revision : this.state.exportRevision, message: result.file ? `Exported progress metadata only: ${result.file.name}. It contains no resumable numerical state or complete portable record.` : 'Progress export cancelled. The partial session is retained.' });
    } catch (error) { if (epoch === this.identityEpoch) this.set({ error: errorText(error) }); }
    finally { this.set({ busy: null }); }
  }
  async export() {
    const summary = this.state.summary; if (!summary || this.state.busy || !summary.canExport) return;
    const requestId = this.id(), epoch = this.identityEpoch; this.set({ busy: 'export', error: '', message: '' });
    try {
      const result = await this.api.export(requestId, summary.sessionId, summary.generation);
      if (epoch !== this.identityEpoch) return;
      if (result.requestId !== requestId || result.sessionId !== summary.sessionId || result.generation !== summary.generation || !ordinal(result.revision)) throw new Error('Export did not match the retained session.');
      this.set({ exported: result.file ?? this.state.exported, exportRevision: result.file ? result.revision : this.state.exportRevision, message: result.file ? `Exported ${result.file.name} · session revision ${result.revision} · SHA-256 ${result.file.sha256}` : 'Export cancelled. The session is retained.' });
    } catch (error) { if (epoch === this.identityEpoch) this.set({ error: errorText(error) }); }
    finally { this.set({ busy: null }); }
  }
  async listenClose() {
    try {
      const unlisten = await this.api.listenClose(() => { this.set({ closeRequested: true }); void this.connect(); });
      // Register first, then read the persistent review flag to close the startup race.
      void this.connect(); return unlisten;
    } catch (error) { this.set({ closeRequested: true, error: `Close review could not attach: ${errorText(error)}` }); return () => {}; }
  }
  async returnToApp() {
    try { await this.api.cancelClose(); this.channelEpoch++; this.set({ closeRequested: false }); void this.connect(); }
    catch (error) { this.set({ error: errorText(error) }); }
  }
  async finishClose(allowDiscard: boolean) {
    if (this.state.busy || this.state.summary?.pendingWrites) return;
    this.set({ busy: 'close', error: '' });
    try { const accepted = await this.api.finishClose(allowDiscard); if (!accepted) this.set({ closeRequested: true, error: 'The backend retained the session because a save is pending or evidence is still unsaved.' }); }
    catch (error) { this.set({ error: errorText(error) }); }
    finally { this.set({ busy: null }); }
  }
  async recovery() {
    const requestId = this.id(), epoch = ++this.recoveryEpoch; this.set({ recoveryBusy: true, recoveryError: '', recoveryMessage: '' });
    try {
      const result = await this.api.recovery(requestId);
      if (epoch !== this.recoveryEpoch) return;
      if (result.requestId !== requestId || result.entries.length > 100) throw new Error('Recovery catalog did not match the bounded request.');
      this.set({ recovery: result });
    } catch (error) { if (epoch === this.recoveryEpoch) this.set({ recoveryError: errorText(error) }); }
    finally { if (epoch === this.recoveryEpoch) this.set({ recoveryBusy: false }); }
  }
  async recovered(sessionId: string) {
    const epoch = ++this.recoveryEpoch; this.set({ recoveryBusy: true, recoveryError: '', recoveryMessage: '' });
    try {
      const result = await this.api.recovered(sessionId);
      if (epoch !== this.recoveryEpoch) return;
      if (result.sessionId !== sessionId || !ordinal(result.generation) || !ordinal(result.revision) || !integer(result.step) || !integer(result.durableStep) || result.durableStep > result.step || !Array.isArray(result.attempts)) throw new Error('Recovery detail did not match the selected checkpoint identity.');
      if (result.pairedBoundary && (!integer(result.pairedBoundary.step, 600) || result.pairedBoundary.step !== result.step || result.pairedBoundary.arms.length !== 2 || new Set(result.pairedBoundary.arms.map(arm => arm.arm)).size !== 2 || result.pairedBoundary.arms.some(arm => !['left', 'right'].includes(arm.arm) || !Number.isInteger(arm.stage) || arm.stage < 1 || arm.stage > 8))) throw new Error('Recovery detail has an invalid paired boundary.');
      this.set({ recovered: result });
    } catch (error) { if (epoch === this.recoveryEpoch) this.set({ recoveryError: errorText(error) }); }
    finally { if (epoch === this.recoveryEpoch) this.set({ recoveryBusy: false }); }
  }
  async exportRecovery(kind: 'record' | 'checkpoint') {
    const selected = this.state.recovered; if (!selected || this.state.recoveryBusy || this.state.busy) return;
    const requestId = this.id(), epoch = ++this.recoveryEpoch; this.set({ recoveryBusy: true, recoveryError: '', recoveryMessage: '' });
    try {
      const result = await this.api.exportRecovery(requestId, selected.sessionId, kind, selected.generation, selected.revision);
      if (epoch !== this.recoveryEpoch) return;
      if (result.requestId !== requestId || result.sessionId !== selected.sessionId || result.generation !== selected.generation || result.revision !== selected.revision || kind === 'record' && result.file !== null && result.file.sha256 !== selected.recordSha256) throw new Error('Recovery export did not match the inspected checkpoint identity.');
      this.set({ recoveryMessage: result.file ? `${kind === 'record' ? `Portable snapshot through durable step ${selected.durableStep}` : 'Recovery checkpoint'} exported: ${result.file.name} · SHA-256 ${result.file.sha256}` : 'Recovery export cancelled. The checkpoint remains selected.' });
    } catch (error) { if (epoch === this.recoveryEpoch) this.set({ recoveryError: errorText(error) }); }
    finally { if (epoch === this.recoveryEpoch) this.set({ recoveryBusy: false }); }
  }
}
export const freshController = new FreshController();
