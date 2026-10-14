import { errorText } from './api';
import type { FileProof, FrameView, OpenRecordResult, RecordExportResult, RecordFrameResult, RecordSummary, RecordTurnResult, TurnView, VerificationReport } from './types';

export interface ReaderApi {
  openRecord(requestId: string, exampleId?: string): Promise<OpenRecordResult>;
  recordFrame(requestId: string, recordId: string, trackId: string, index: number): Promise<RecordFrameResult>;
  recordTurn(requestId: string, recordId: string, trackId: string, index: number): Promise<RecordTurnResult>;
  exportRecord(requestId: string, recordId: string): Promise<RecordExportResult>;
  closeRecord(recordId: string): Promise<void>;
}
export interface ReaderState {
  record: RecordSummary | null; frame: FrameView | null; trackId: string | null; cursors: Record<string, number>;
  turn: TurnView | null; opening: boolean; loadingFrame: boolean; loadingTurn: boolean; exporting: boolean;
  playing: boolean; message: string; report: VerificationReport | null; exported: FileProof | null;
}
let requestSequence = 0;
const requestId = () => `record-reader-${++requestSequence}`;
const empty = (): ReaderState => ({ record: null, frame: null, trackId: null, cursors: {}, turn: null, opening: false,
  loadingFrame: false, loadingTurn: false, exporting: false, playing: false, message: '', report: null, exported: null });

/** Own accepted reading state independently of in-flight replacements. */
export class RecordingController {
  private state = empty();
  private listeners = new Set<() => void>();
  private openGeneration = 0;
  private frameGeneration = 0;
  private turnGeneration = 0;
  private exportGeneration = 0;
  constructor(private api: ReaderApi) {}
  snapshot = () => this.state;
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  private update(next: Partial<ReaderState>) { this.state = { ...this.state, ...next }; this.listeners.forEach(listener => listener()); }
  private async release(id: string) { try { await this.api.closeRecord(id); } catch { /* Stale-handle cleanup cannot replace an accepted reading. */ } }

  open(exampleId?: string) { return this.replace(id => this.api.openRecord(id, exampleId)); }
  adopt(record: RecordSummary) {
    if (record.recordId === this.state.record?.recordId) return Promise.resolve();
    return this.replace(async requestId => ({ requestId, cancelled: false, report: record.verification, record }));
  }

  private async replace(load: (requestId: string) => Promise<OpenRecordResult>) {
    const generation = ++this.openGeneration;
    this.update({ opening: true, playing: false, message: 'Checking the selected recording…', report: null });
    let candidate: RecordSummary | null = null;
    try {
      const request = requestId();
      const result = await load(request);
      candidate = result.record;
      if (generation !== this.openGeneration) { if (candidate) await this.release(candidate.recordId); return; }
      if (result.requestId !== request) throw new Error('The open response did not match its request.');
      if (result.cancelled) { this.update({ opening: false, message: 'Open cancelled. The current reading is unchanged.' }); return; }
      if (!candidate || result.report?.status !== 'passed') {
        if (candidate) await this.release(candidate.recordId);
        this.update({ opening: false, report: result.report, message: 'The incoming recording was not accepted. The current reading is unchanged.' }); return;
      }
      const track = candidate.tracks.find(item => item.frameCount > 0) ?? candidate.tracks[0];
      let first: FrameView | null = null;
      if (track && track.frameCount > 0) {
        const frameRequest = requestId();
        const response = await this.api.recordFrame(frameRequest, candidate.recordId, track.id, 0);
        if (response.requestId !== frameRequest || response.recordId !== candidate.recordId || response.trackId !== track.id || response.frame.index !== 0) throw new Error('The initial frame did not match the accepted recording.');
        first = response.frame;
      }
      if (generation !== this.openGeneration) { await this.release(candidate.recordId); return; }
      const previous = this.state.record;
      this.frameGeneration++; this.turnGeneration++; this.exportGeneration++;
      this.update({ ...empty(), record: candidate, frame: first, trackId: track?.id ?? null, cursors: track ? { [track.id]: 0 } : {}, report: result.report,
        message: first ? 'Recorded evidence opened. No model was contacted.' : 'Verified recording opened with no retained frames. Identity, available turns and original-byte export remain accessible.' });
      if (previous) await this.release(previous.recordId);
    } catch (error) {
      if (candidate) await this.release(candidate.recordId);
      if (generation === this.openGeneration) this.update({ opening: false, message: `${errorText(error)} The current reading is unchanged.` });
    }
  }

  async seek(index: number, trackId = this.state.trackId) {
    const record = this.state.record;
    const track = record?.tracks.find(item => item.id === trackId);
    if (!record || !track || track.frameCount < 1 || !Number.isFinite(index)) return;
    const target = Math.max(0, Math.min(track.frameCount - 1, Math.round(index)));
    const generation = ++this.frameGeneration;
    const request = requestId();
    this.update({ loadingFrame: true, message: '' });
    try {
      const result = await this.api.recordFrame(request, record.recordId, track.id, target);
      if (generation !== this.frameGeneration || this.state.record?.recordId !== record.recordId) return;
      if (result.requestId !== request || result.recordId !== record.recordId || result.trackId !== track.id || result.frame.index !== target) throw new Error('The frame response did not match the current request.');
      const changedTrack = this.state.trackId !== track.id;
      if (changedTrack) this.turnGeneration++;
      this.update({ frame: result.frame, trackId: track.id, cursors: { ...this.state.cursors, [track.id]: target }, loadingFrame: false,
        ...(changedTrack ? { turn: null, loadingTurn: false } : {}), playing: this.state.playing && target < track.frameCount - 1 });
    } catch (error) {
      if (generation === this.frameGeneration && this.state.record?.recordId === record.recordId) this.update({ loadingFrame: false, playing: false, message: `${errorText(error)} The last readable frame is retained.` });
    }
  }

  selectTrack(id: string) {
    this.pause();
    const track = this.state.record?.tracks.find(item => item.id === id);
    if (track?.frameCount === 0) {
      this.frameGeneration++; this.turnGeneration++;
      this.update({ trackId: id, frame: null, turn: null, loadingFrame: false, loadingTurn: false, message: 'This recorded track has no retained frames.' });
      return Promise.resolve();
    }
    return this.seek(this.state.cursors[id] ?? 0, id);
  }
  play() { const track = this.state.record?.tracks.find(item => item.id === this.state.trackId); if (track && this.state.frame && this.state.frame.index < track.frameCount - 1) this.update({ playing: true }); }
  pause() { if (this.state.playing) this.update({ playing: false }); }

  async turn(index: number) {
    const record = this.state.record;
    const track = record?.tracks.find(item => item.id === this.state.trackId);
    if (!record || !track || index < 0 || index >= track.turnCount) return;
    const generation = ++this.turnGeneration;
    const request = requestId();
    this.update({ loadingTurn: true });
    try {
      const result = await this.api.recordTurn(request, record.recordId, track.id, index);
      if (generation !== this.turnGeneration || this.state.record?.recordId !== record.recordId || this.state.trackId !== track.id) return;
      if (result.requestId !== request || result.recordId !== record.recordId || result.trackId !== track.id || result.turn.index !== index) throw new Error('The turn response did not match the selected recording.');
      this.update({ turn: result.turn, loadingTurn: false });
    } catch (error) { if (generation === this.turnGeneration) this.update({ loadingTurn: false, message: errorText(error) }); }
  }

  async export() {
    const record = this.state.record;
    if (!record || this.state.exporting) return;
    const generation = ++this.exportGeneration;
    const request = requestId();
    this.update({ exporting: true });
    try {
      const result = await this.api.exportRecord(request, record.recordId);
      if (generation !== this.exportGeneration || this.state.record?.recordId !== record.recordId) return;
      if (result.requestId !== request || result.recordId !== record.recordId) throw new Error('The export response did not match the current recording.');
      this.update({ exporting: false, exported: result.file ?? this.state.exported, message: result.file ? 'Original recording bytes exported.' : 'Export cancelled. The recording is unchanged.' });
    } catch (error) { if (generation === this.exportGeneration) this.update({ exporting: false, message: errorText(error) }); }
  }

  async close() {
    this.openGeneration++; this.frameGeneration++; this.turnGeneration++; this.exportGeneration++;
    const previous = this.state.record;
    this.state = empty(); this.listeners.forEach(listener => listener());
    if (previous) await this.release(previous.recordId);
  }
}
