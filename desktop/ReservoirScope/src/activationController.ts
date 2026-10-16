import { errorText } from './api';
import { activationApi } from './activationApi';
import { activationCanStart, activationRunning, type ActivationAnnotation, type ActivationApi, type ActivationCapability, type ActivationConfig, type ActivationSnapshot } from './activationTypes';

export interface ActivationState {
  current: ActivationSnapshot | null; saved: ActivationSnapshot[]; comparisons: ActivationSnapshot[];
  capability: ActivationCapability | null; checkedConfig: string | null; busy: string | null;
  error: string; message: string; revealed: boolean;
  selected: Record<string, string>; following: Record<string, boolean>;
}
const empty = (): ActivationState => ({ current: null, saved: [], comparisons: [], capability: null, checkedConfig: null, busy: null, error: '', message: '', revealed: false, selected: {}, following: {} });
const integer = (value: unknown) => typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
export function validateActivationSnapshot(value: ActivationSnapshot) {
  if (!value || !value.sessionId || !integer(value.revision) || !integer(value.step) || !integer(value.observationIndex) || !integer(value.journalCount)
    || typeof value.status !== 'string' || value.activeOperation !== null && typeof value.activeOperation !== 'string'
    || !value.config || !['no_steering', 'decaying_trace', 'recurrent'].includes(value.config.arm)
    || !Array.isArray(value.journals) || value.journals.length > 100 || !Array.isArray(value.events) || value.events.length > 10000
    || value.journalCount !== value.journals.length || new Set(value.journals.map(j => j.id)).size !== value.journals.length
    || new Set(value.events.map(e => e.id)).size !== value.events.length
    || value.journals.some(j => !j.id || typeof j.text !== 'string' || !integer(j.observedStep) || j.firstAppliedStep !== null && (!integer(j.firstAppliedStep) || j.firstAppliedStep <= j.observedStep))
    || value.events.some(e => !e.id || typeof e.kind !== 'string' || typeof e.detail !== 'string' || !integer(e.step))) throw new Error('The activation record has invalid identities, journal bounds or application steps.');
}

/** The backend advances the experiment. Reading and polling never dispatch model work. */
export class ActivationController {
  private state = empty(); private listeners = new Set<() => void>(); private active = false;
  private timer: ReturnType<typeof setTimeout> | null = null; private epoch = 0; private pollEpoch = 0;
  constructor(private api: ActivationApi = activationApi, private interval = 1000) {}
  snapshot = () => this.state;
  subscribe = (fn: () => void) => { this.listeners.add(fn); return () => { this.listeners.delete(fn); }; };
  private set(patch: Partial<ActivationState>) { this.state = { ...this.state, ...patch }; this.listeners.forEach(fn => fn()); }
  private cancelPoll() { if (this.timer !== null) clearTimeout(this.timer); this.timer = null; this.pollEpoch++; }
  setActive(active: boolean) { this.active = active; this.cancelPoll(); if (active) this.schedule(); }
  private schedule() {
    if (!this.active || !activationRunning(this.state.current) || this.timer !== null || this.state.busy) return;
    this.timer = setTimeout(() => { this.timer = null; void this.refresh(); }, this.interval);
  }
  private accept(snapshot: ActivationSnapshot, replacement = false) {
    validateActivationSnapshot(snapshot);
    const prior = this.state.current;
    if (!replacement && prior?.sessionId !== snapshot.sessionId) throw new Error('The response belongs to another activation session.');
    if (prior?.sessionId === snapshot.sessionId && snapshot.revision < prior.revision) return;
    const selected = { ...this.state.selected }, following = { ...this.state.following };
    if (following[snapshot.sessionId] !== false) {
      following[snapshot.sessionId] = true;
      const latest = snapshot.journals.at(-1); if (latest) selected[snapshot.sessionId] = latest.id;
    }
    const comparisons = this.state.comparisons.map(s => s.sessionId === snapshot.sessionId ? snapshot : s);
    if (!comparisons.some(s => s.sessionId === snapshot.sessionId) && comparisons.length < 3) comparisons.push(snapshot);
    const saved = this.state.saved.map(s => s.sessionId === snapshot.sessionId ? snapshot : s);
    this.set({ current: snapshot, comparisons, saved, selected, following, ...(prior?.sessionId !== snapshot.sessionId ? { revealed: false } : {}) });
  }
  async inspect(config: ActivationConfig) {
    if (this.state.busy) return null;
    const epoch = ++this.epoch; this.set({ busy: 'inspect', error: '', capability: null, checkedConfig: null });
    try {
      const result = await this.api.inspect(config); if (epoch !== this.epoch) return null;
      this.set({ capability: result, checkedConfig: JSON.stringify(result.config ?? config) }); return result;
    } catch (e) { this.set({ error: errorText(e) }); return null; }
    finally { if (epoch === this.epoch) { this.set({ busy: null }); this.schedule(); } }
  }
  async create(config: ActivationConfig) {
    if (this.state.busy || activationRunning(this.state.current)) return false;
    if (this.state.checkedConfig !== JSON.stringify(config) || this.state.capability?.ready === false) { this.set({ error: 'Check these exact settings and resolve setup failures before preparing the experiment.' }); return false; }
    return this.operation('create', () => this.api.create(config), true, 'Prepared locally. Choose Start to load the model and run this condition.');
  }
  async start() {
    const s = this.state.current; if (!s || !activationCanStart(s) || activationRunning(s)) return false;
    return this.operation('start', () => this.api.start(s.sessionId), false, 'The bounded experiment is running.');
  }
  async stop() {
    const s = this.state.current; if (!s || !activationRunning(s)) return false;
    return this.operation('stop', () => this.api.stop(s.sessionId), false, 'Stopped. Retained writing and events remain available.');
  }
  private async operation(name: string, call: () => Promise<ActivationSnapshot>, replacement = false, message = '') {
    if (this.state.busy) return false;
    const epoch = ++this.epoch; this.cancelPoll(); this.set({ busy: name, error: '', message: '' });
    try {
      const result = await call(); if (epoch !== this.epoch) return false;
      this.accept(result, replacement); this.set({ message }); return true;
    } catch (e) { if (epoch === this.epoch) this.set({ error: errorText(e) }); return false; }
    finally { if (epoch === this.epoch) { this.set({ busy: null }); this.schedule(); } }
  }
  async refresh() {
    const s = this.state.current; if (!s || this.state.busy) return;
    const epoch = ++this.pollEpoch, identity = this.epoch;
    try {
      const result = await this.api.get(s.sessionId);
      if (epoch !== this.pollEpoch || identity !== this.epoch || this.state.current?.sessionId !== s.sessionId) return;
      if (!result) throw new Error('The current activation session is unavailable. Retained reading is unchanged.');
      this.accept(result); this.schedule();
    } catch (e) { if (epoch === this.pollEpoch && identity === this.epoch) { this.cancelPoll(); this.set({ error: `${errorText(e)} Use Refresh to check again.` }); } }
  }
  async list() {
    if (this.state.busy) return;
    this.set({ busy: 'list', error: '' });
    try { const saved = await this.api.list(); if (saved.length > 1000) throw new Error('Too many saved sessions in one response.'); saved.forEach(validateActivationSnapshot); this.set({ saved }); }
    catch (e) { this.set({ error: errorText(e) }); }
    finally { this.set({ busy: null }); this.schedule(); }
  }
  compare(session: ActivationSnapshot, include: boolean) {
    validateActivationSnapshot(session);
    const exists = this.state.comparisons.some(s => s.sessionId === session.sessionId);
    if (include && !exists && this.state.comparisons.length >= 3) { this.set({ error: 'Select at most three runs for this comparison.' }); return; }
    const comparisons = include ? exists ? this.state.comparisons : [...this.state.comparisons, session] : this.state.comparisons.filter(s => s.sessionId !== session.sessionId);
    const latest = session.journals.at(-1);
    this.set({ comparisons, revealed: false, selected: latest && !this.state.selected[session.sessionId] ? { ...this.state.selected, [session.sessionId]: latest.id } : this.state.selected });
  }
  select(sessionId: string, journalId: string) {
    const s = this.state.comparisons.find(s => s.sessionId === sessionId);
    if (!s?.journals.some(j => j.id === journalId)) return;
    this.set({ selected: { ...this.state.selected, [sessionId]: journalId }, following: { ...this.state.following, [sessionId]: false } });
  }
  adjacent(sessionId: string, direction: -1 | 1) {
    const s = this.state.comparisons.find(s => s.sessionId === sessionId); if (!s) return;
    const i = s.journals.findIndex(j => j.id === this.state.selected[sessionId]); const next = s.journals[i + direction];
    if (next) this.select(sessionId, next.id);
  }
  follow(sessionId: string) {
    const s = this.state.comparisons.find(s => s.sessionId === sessionId), latest = s?.journals.at(-1);
    this.set({ following: { ...this.state.following, [sessionId]: true }, selected: latest ? { ...this.state.selected, [sessionId]: latest.id } : this.state.selected });
  }
  reveal() { this.set({ revealed: true }); }
  restore(sessionId: string) {
    if (activationRunning(this.state.current)) return Promise.resolve(false);
    return this.operation('restore', () => this.api.restore(sessionId), true, 'Restored for review. No model request was started.');
  }
  async export(sessionId: string) {
    if (this.state.busy || activationRunning(this.state.current)) return;
    this.set({ busy: 'export', error: '', message: '' });
    try { const r = await this.api.export(sessionId); this.set({ message: r.path ? `${r.verified ? 'Verified export saved' : 'Export saved; verification incomplete'}: ${r.path}` : 'Export cancelled.' }); }
    catch (e) { this.set({ error: errorText(e) }); }
    finally { this.set({ busy: null }); this.schedule(); }
  }
  async import() {
    if (this.state.busy || activationRunning(this.state.current)) return;
    const epoch = ++this.epoch; this.cancelPoll(); this.set({ busy: 'import', error: '', message: '' });
    try { const s = await this.api.import(); if (epoch !== this.epoch) return; if (s) { this.accept(s, true); this.set({ message: 'Imported for paused review. No model request was started.' }); } }
    catch (e) { this.set({ error: errorText(e) }); }
    finally { this.set({ busy: null }); }
  }
  async annotate(sessionId: string, annotation: ActivationAnnotation) {
    if (this.state.busy) return false;
    const session = this.state.comparisons.find(s => s.sessionId === sessionId);
    if (!session || !annotation.interpretation.trim() || !annotation.alternative.trim() || !annotation.sourceEventIds.length
      || annotation.sourceEventIds.some(id => !session.events.some(e => e.id === id))
      || annotation.excerpt && !session.journals.find(j => j.id === annotation.journalId)?.text.includes(annotation.excerpt)) {
      this.set({ error: 'Add an interpretation, another possible reading, and source events. A quoted excerpt must match the selected journal exactly.' }); return false;
    }
    this.set({ busy: 'annotation', error: '' });
    try {
      const result = await this.api.annotate(sessionId, annotation); validateActivationSnapshot(result);
      if (result.sessionId !== sessionId) throw new Error('The saved annotation belongs to another session.');
      if (this.state.current?.sessionId === sessionId) this.accept(result);
      else this.set({ comparisons: this.state.comparisons.map(s => s.sessionId === sessionId ? result : s) });
      this.set({ message: 'Reading note saved separately. It is never supplied as model feedback.' }); return true;
    } catch (e) { this.set({ error: errorText(e) }); return false; }
    finally { this.set({ busy: null }); this.schedule(); }
  }
}
export const activationController = new ActivationController();
