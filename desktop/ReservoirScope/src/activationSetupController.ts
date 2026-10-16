import { errorText } from './api';
import { activationSetupApi } from './activationSetupApi';
import { activationSetupCanPrepare, activationSetupCanResume, validateActivationSetupStatus, type ActivationSetupApi, type ActivationSetupStatus, type ActivationSetupViewState } from './activationSetupTypes';

/** Only explicit Prepare/Resume dispatch installation. Status reads never resume work. */
export class ActivationSetupController {
  private state: ActivationSetupViewState = { status: null, pending: null, checking: false, error: '' };
  private listeners = new Set<() => void>();
  private active = false;
  private timer: ReturnType<typeof setTimeout> | null = null;
  private epoch = 0;
  private readId = 0;

  constructor(private api: ActivationSetupApi = activationSetupApi, private interval = 1000) {}
  snapshot = () => this.state;
  subscribe = (fn: () => void) => { this.listeners.add(fn); return () => { this.listeners.delete(fn); }; };

  private set(patch: Partial<ActivationSetupViewState>) {
    this.state = { ...this.state, ...patch };
    this.listeners.forEach(fn => fn());
  }

  private clearPoll() {
    if (this.timer !== null) clearTimeout(this.timer);
    this.timer = null;
  }

  private schedule() {
    if (!this.active || this.state.status?.state !== 'preparing' || this.state.pending || this.state.checking || this.state.error || this.timer !== null) return;
    this.timer = setTimeout(() => { this.timer = null; void this.refresh(); }, this.interval);
  }

  setActive(active: boolean) {
    this.active = active;
    this.clearPoll();
    if (active) void this.refresh();
  }

  async refresh() {
    if (this.state.pending || this.state.checking) return;
    this.clearPoll();
    const id = ++this.readId, epoch = this.epoch;
    this.set({ checking: true, error: '' });
    try {
      const status = await this.api.status();
      if (id !== this.readId || epoch !== this.epoch) return;
      validateActivationSetupStatus(status);
      this.set({ status });
    } catch (error) {
      if (id === this.readId && epoch === this.epoch) this.set({ error: `${errorText(error)} Use Check setup status to try the read again.` });
    } finally {
      if (id === this.readId && epoch === this.epoch) { this.set({ checking: false }); this.schedule(); }
    }
  }

  async prepare(resume = false) {
    if (this.state.pending || this.state.checking || this.state.error || !(resume ? activationSetupCanResume(this.state.status) : activationSetupCanPrepare(this.state.status))) return false;
    return this.operation(resume ? 'resume' : 'prepare', () => this.api.prepare(resume));
  }

  async cancel() {
    if (this.state.pending || this.state.status?.state !== 'preparing') return false;
    return this.operation('cancel', () => this.api.cancel());
  }

  private async operation(pending: NonNullable<ActivationSetupViewState['pending']>, call: () => Promise<ActivationSetupStatus>) {
    const epoch = ++this.epoch;
    ++this.readId;
    this.clearPoll();
    this.set({ pending, checking: false, error: '' });
    try {
      const status = await call();
      if (epoch !== this.epoch) return false;
      validateActivationSetupStatus(status);
      this.set({ status });
      return true;
    } catch (error) {
      if (epoch === this.epoch) this.set({ error: `${errorText(error)} Check setup status before trying again.` });
      return false;
    } finally {
      if (epoch === this.epoch) { this.set({ pending: null }); this.schedule(); }
    }
  }
}
