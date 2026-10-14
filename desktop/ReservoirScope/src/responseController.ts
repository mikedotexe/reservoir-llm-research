import { errorText } from './api';
import type { FileProof } from './types';
import type { ResponseApi, ResponseEventDetail, ResponseField, ResponseFrame, ResponseFrameResult, ResponseSource, ResponseSummary } from './responseTypes';

export interface ResponseReading {
  summary: ResponseSummary | null; frame: ResponseFrame | null; event: ResponseEventDetail | null;
  node: number; field: ResponseField; opening: boolean; loading: boolean; loadingEvent: boolean;
  exporting: boolean; exported: FileProof | null; playing: boolean; rate: number; message: string;
}
const empty = (): ResponseReading => ({ summary: null, frame: null, event: null, node: 0, field: 'delta', opening: false, loading: false, loadingEvent: false, exporting: false, exported: null, playing: false, rate: 3, message: '' });
let sequence = 0;
const request = () => `response-${++sequence}`;
const vector = (values: number[] | null, bounded = false): boolean => Array.isArray(values) && values.length === 128 && values.every(value => Number.isFinite(value) && (!bounded || Math.abs(value) <= 1));

function checkSummary(summary: ResponseSummary, source: ResponseSource) {
  if (summary.kind !== (source === 'simulation-example' ? 'simulation' : 'native') || summary.origin !== (source === 'native-file' ? 'openedFile' : 'bundled') || !summary.responseId || summary.nodeCount !== 128 || !Number.isInteger(summary.frameCount) || summary.frameCount < 0 || summary.frameCount > 1024 || !Number.isFinite(summary.fixedDeltaScale) || summary.fixedDeltaScale <= 0 || (summary.returnThreshold !== null && (!Number.isFinite(summary.returnThreshold) || summary.returnThreshold < 0)) || summary.timeline.length !== summary.frameCount || summary.timeline.some((point, index) => point.index !== index || !/^[0-9]{1,20}$/.test(point.position) || !Number.isFinite(point.l2) || point.l2 < 0) || summary.events.length > 1024 || summary.events.some((event, index) => event.index !== index)) throw new Error('Response summary did not match the explicit source and bounded coverage.');
}
function checkFrame(result: ResponseFrameResult, id: string, summary: ResponseSummary, index: number) {
  const frame = result.frame, point = summary.timeline[index];
  if (result.requestId !== id || result.responseId !== summary.responseId || frame.index !== index || frame.position !== point?.position || frame.l2 !== point?.l2 || !vector(frame.first, true) || !vector(frame.second, true) || !vector(frame.delta) || (frame.direction !== null && !vector(frame.direction)) || (frame.realizedNoise !== null && !vector(frame.realizedNoise))) throw new Error('Response frame did not match the accepted evidence and requested boundary.');
}

/** Accepted evidence stays immutable; every asynchronous view has a generation. */
export class ResponseController {
  private state = empty();
  private listeners = new Set<() => void>();
  private openGeneration = 0; private frameGeneration = 0; private eventGeneration = 0; private exportGeneration = 0;
  private clock: { time: number; position: number } | null = null;
  constructor(private api: ResponseApi) {}
  snapshot = () => this.state;
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  private update(change: Partial<ResponseReading>) { this.state = { ...this.state, ...change }; this.listeners.forEach(listener => listener()); }
  private async release(id: string) { try { await this.api.close(id); } catch { /* Cleanup cannot replace a newer accepted reading. */ } }
  async open(source: ResponseSource) {
    if (this.state.exporting) return;
    const generation = ++this.openGeneration; this.pause();
    this.update({ opening: true, message: 'Checking response identity, coordinates and retained measurements…' });
    let candidate: ResponseSummary | null = null;
    try {
      const id = request(), result = await this.api.open(id, source, this.state.summary?.responseId ?? null);
      candidate = result.response;
      if (generation !== this.openGeneration) { if (candidate) await this.release(candidate.responseId); return; }
      if (result.requestId !== id) throw new Error('Response open did not match its request.');
      if (result.cancelled) {
        if (candidate) { await this.release(candidate.responseId); candidate = null; }
        this.update({ opening: false, message: 'Open cancelled. The accepted evidence and selection are unchanged.' }); return;
      }
      if (!candidate) throw new Error('No validated response evidence was returned.');
      checkSummary(candidate, source);
      let frame: ResponseFrame | null = null;
      if (candidate.frameCount > 0) {
        const frameId = request(), result = await this.api.frame(frameId, candidate.responseId, 0);
        if (generation !== this.openGeneration) { await this.release(candidate.responseId); return; }
        checkFrame(result, frameId, candidate, 0); frame = result.frame;
      }
      const old = this.state.summary;
      this.frameGeneration++; this.eventGeneration++; this.exportGeneration++;
      this.update({ ...empty(), summary: candidate, frame, message: candidate.frameCount ? 'Retained response accepted. Exact values and source limits are available below.' : 'This bundle contains events but no applied state frame. Admission or terminal events do not establish a state change.' });
      candidate = null;
      if (old) await this.release(old.responseId);
    } catch (error) {
      if (candidate) await this.release(candidate.responseId);
      if (generation === this.openGeneration) this.update({ opening: false, message: `${errorText(error)} The accepted evidence and selection are unchanged.` });
    }
  }
  selectNode(node: number) { if (Number.isInteger(node) && node >= 0 && node < 128) this.update({ node }); }
  selectField(field: ResponseField) { this.update({ field }); }
  async selectEvent(index: number) {
    const summary = this.state.summary;
    if (!summary || !Number.isInteger(index) || index < 0 || index >= summary.events.length) return;
    const generation = ++this.eventGeneration, id = request(); this.update({ loadingEvent: true });
    try {
      const result = await this.api.event(id, summary.responseId, index);
      if (generation !== this.eventGeneration) return;
      const event = result.event, expected = summary.events[index];
      if (result.requestId !== id || result.responseId !== summary.responseId || event.index !== index || event.status !== expected.status || event.isBoundary !== expected.isBoundary || event.hasState !== (expected.frameIndex !== null) || !vector(event.direction) || (event.realizedNoise !== null && !vector(event.realizedNoise)) || (event.first !== null && !vector(event.first, true)) || (event.second !== null && !vector(event.second, true)) || (event.delta !== null && !vector(event.delta))) throw new Error('Event detail did not match the selected receipt.');
      this.update({ event, loadingEvent: false });
    } catch (error) { if (generation === this.eventGeneration) this.update({ loadingEvent: false, message: `${errorText(error)} The last readable receipt detail is retained.` }); }
  }
  async frame(index: number) {
    this.pause(); const summary = this.state.summary;
    if (!summary || !summary.frameCount || !Number.isFinite(index)) return;
    await this.read(Math.max(0, Math.min(summary.frameCount - 1, Math.round(index))));
  }
  private async read(index: number) {
    const summary = this.state.summary; if (!summary) return;
    const generation = ++this.frameGeneration, id = request(); this.update({ loading: true });
    try {
      const result = await this.api.frame(id, summary.responseId, index);
      if (generation !== this.frameGeneration) return;
      checkFrame(result, id, summary, index);
      this.update({ frame: this.state.frame?.index === index ? this.state.frame : result.frame, loading: false });
    } catch (error) { if (generation === this.frameGeneration) { this.pause(); this.update({ loading: false, message: `${errorText(error)} The last readable boundary is retained.` }); } }
  }
  setRate(rate: number) { if ([0.5, 1, 2, 3, 4, 8].includes(rate)) { this.pause(); this.update({ rate }); } }
  play(now: number) {
    const { summary, frame, loading, opening } = this.state;
    if (!summary || !frame || loading || opening || frame.index >= summary.frameCount - 1 || !Number.isFinite(now)) return;
    this.clock = { time: now, position: frame.index }; this.update({ playing: true });
  }
  pause() { if (this.clock) { this.frameGeneration++; this.update({ loading: false }); } this.clock = null; if (this.state.playing) this.update({ playing: false }); }
  async tick(now: number) {
    const { summary, playing, frame } = this.state, clock = this.clock;
    if (!summary || !playing || !clock || !frame || !Number.isFinite(now)) return;
    clock.position = Math.min(summary.frameCount - 1, clock.position + Math.max(0, now - clock.time) / 1000 * this.state.rate); clock.time = Math.max(now, clock.time);
    if (this.state.loading) return;
    const target = Math.floor(clock.position);
    if (target !== frame.index) await this.read(target);
    if (this.clock === clock && target >= summary.frameCount - 1) this.pause();
  }
  async export() {
    const summary = this.state.summary; if (!summary || this.state.exporting || this.state.opening) return;
    const generation = ++this.exportGeneration, id = request(); this.pause(); this.update({ exporting: true });
    try {
      const result = await this.api.export(id, summary.responseId);
      if (generation !== this.exportGeneration) return;
      if (result.requestId !== id || result.responseId !== summary.responseId || (result.file && (result.file.sha256 !== summary.sha256 || result.file.sizeBytes !== summary.sizeBytes))) throw new Error('Export identity did not match the original accepted bytes.');
      this.update({ exporting: false, exported: result.file ?? this.state.exported, message: result.file ? 'Original response bytes exported without reconstructing JSON.' : 'Export cancelled. Accepted evidence is unchanged.' });
    } catch (error) { if (generation === this.exportGeneration) this.update({ exporting: false, message: errorText(error) }); }
  }
  async close() {
    this.openGeneration++; this.frameGeneration++; this.eventGeneration++; this.exportGeneration++; this.pause();
    const old = this.state.summary; this.update(empty()); if (old) await this.release(old.responseId);
  }
}
