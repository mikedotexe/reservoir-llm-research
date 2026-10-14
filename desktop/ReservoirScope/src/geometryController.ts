import { errorText } from './api';
import type { GeometryApi, GeometryPacket } from './geometryTypes';
import type { FileProof } from './types';

export interface GeometryReading {
  packet: GeometryPacket | null; selected: number; frame: number; coordinate: number; coordinatesExpanded: boolean;
  busy: boolean; message: string; exported: FileProof | null;
}
/** Window-memory reading state, independent of view visibility. No polling or storage. */
export class GeometryController {
  private state: GeometryReading = { packet: null, selected: 0, frame: 0, coordinate: 0, coordinatesExpanded: false, busy: false, message: '', exported: null };
  private sequence = 0;
  private listeners = new Set<() => void>();
  constructor(private api: GeometryApi) {}
  snapshot = () => this.state;
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  private update(change: Partial<GeometryReading>) { this.state = { ...this.state, ...change }; this.listeners.forEach(listener => listener()); }
  async open(syntheticExample = false) {
    if (this.state.busy) return;
    const request = `geometry-${++this.sequence}`;
    this.update({ busy: true, message: 'Checking packet integrity, references, clocks and coordinates…' });
    try {
      const result = await this.api.open(request, syntheticExample);
      if (result.requestId !== request) throw new Error('The geometry response did not match this request.');
      if (result.cancelled) { this.update({ message: 'Open cancelled. The current packet and reading position are unchanged.' }); return; }
      if (!result.packet) throw new Error('No validated geometry packet was returned.');
      if (result.packet.origin !== (syntheticExample ? 'syntheticExample' : 'openedFile')) throw new Error('The packet origin did not match the explicit open operation.');
      this.update({ packet: result.packet, selected: 0, frame: 0, coordinate: 0, coordinatesExpanded: false, exported: null, message: 'Packet integrity checked. Producer authenticity and historical novelty are not established.' });
    } catch (error) { this.update({ message: `${errorText(error)} The current packet and reading position are unchanged.` }); }
    finally { this.update({ busy: false }); }
  }
  select(index: number) {
    if (Number.isInteger(index) && this.state.packet && index >= 0 && index < this.state.packet.records.length) this.update({ selected: index, frame: 0 });
  }
  seek(index: number) {
    const frames = this.state.packet?.records[this.state.selected]?.snapshot?.frames;
    if (frames && Number.isFinite(index)) this.update({ frame: Math.max(0, Math.min(frames.length - 1, Math.round(index))) });
  }
  coordinate(index: number) { if (Number.isInteger(index) && index >= 0 && index < 128) this.update({ coordinate: index }); }
  expand(value: boolean) { this.update({ coordinatesExpanded: value }); }
  async export() {
    const packet = this.state.packet;
    if (!packet || this.state.busy) return;
    const request = `geometry-${++this.sequence}`;
    this.update({ busy: true });
    try {
      const result = await this.api.export(request, packet.packetId);
      if (result.requestId !== request || result.packetId !== packet.packetId) throw new Error('The export response did not match the current packet.');
      if (result.file && (result.file.sha256 !== packet.sha256 || result.file.sizeBytes !== packet.sizeBytes)) throw new Error('The export identity does not match the original packet bytes.');
      this.update({ exported: result.file ?? this.state.exported, message: result.file ? 'Original packet bytes exported; the JSON was not reconstructed.' : 'Export cancelled. The packet is unchanged.' });
    } catch (error) { this.update({ message: errorText(error) }); }
    finally { this.update({ busy: false }); }
  }
}
