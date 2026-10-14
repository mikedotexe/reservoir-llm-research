import { errorText } from './api';
import { preparationApi } from './preparationApi';
import type { PreparationApi, PreparationExample, PreparationReport, PreparationReportSummary } from './preparationTypes';

export interface PreparationState {
  reports: PreparationReportSummary[]; examples: PreparationExample[]; loaded: boolean;
  selected: { summary: PreparationReportSummary; report: PreparationReport; retainedExampleId: string | null; retainedExampleDiagnostic: string | null } | null;
  busy: boolean; pendingId: string | null; exporting: boolean; error: string; message: string;
}
let nextControllerId = 0;
export class PreparationController {
  private state: PreparationState = { reports: [], examples: [], loaded: false, selected: null, busy: false, pendingId: null, exporting: false, error: '', message: '' };
  private listeners = new Set<() => void>();
  private active = false;
  private generation = 0;
  private selection = 0;
  private serial = 0;
  private readonly instance = ++nextControllerId;
  constructor(private api: PreparationApi = preparationApi) {}
  snapshot = () => this.state;
  subscribe = (fn: () => void) => { this.listeners.add(fn); return () => { this.listeners.delete(fn); }; };
  private set(patch: Partial<PreparationState>) { this.state = { ...this.state, ...patch }; this.listeners.forEach(fn => fn()); }
  private id() { return `preparation-${this.instance}-${++this.serial}`; }
  activate(active: boolean) {
    if (this.active === active) return;
    this.active = active;
    if (!active) {
      this.generation++; this.selection++;
      this.set({ busy: false, pendingId: null, message: '' });
    } else if (!this.state.loaded || !this.state.selected) void this.refresh();
  }
  async refresh() {
    if (!this.active || this.state.busy) return;
    const generation = ++this.generation; ++this.selection;
    const requestId = this.id();
    this.set({ busy: true, pendingId: null, error: '', message: '' });
    try {
      const result = await this.api.list(requestId);
      if (!this.active || generation !== this.generation) return;
      if (result.requestId !== requestId) throw new Error('Preparation history response did not match this request.');
      this.set({ reports: result.reports, examples: result.examples, loaded: true });
      const selected = this.state.selected;
      if (!selected || !result.reports.some(r => r.id === selected.summary.id && r.sha256 === selected.summary.sha256)) {
        if (result.reports[0]) await this.select(result.reports[0]);
      }
    } catch (error) {
      if (this.active && generation === this.generation) this.set({ error: errorText(error), message: 'History could not be refreshed. Any previously accepted report remains available.' });
    } finally {
      if (generation === this.generation) this.set({ busy: false });
    }
  }
  async select(summary: PreparationReportSummary) {
    if (!this.active) return;
    const selection = ++this.selection, generation = this.generation, requestId = this.id();
    const current = () => this.active && generation === this.generation && selection === this.selection;
    this.set({ pendingId: summary.id, error: '', message: '' });
    try {
      const result = await this.api.get(requestId, summary.id);
      if (!current()) return;
      if (result.requestId !== requestId || result.reportId !== summary.id || result.sha256 !== summary.sha256 || result.report.status !== summary.status) throw new Error('Preparation report response did not match the selected report identity.');
      this.set({ selected: { summary, report: result.report, retainedExampleId: result.retainedExampleId, retainedExampleDiagnostic: result.retainedExampleDiagnostic } });
    } catch (error) {
      if (current()) this.set({ error: errorText(error), message: 'Report details could not be read. Any previously accepted report remains selected.' });
    } finally {
      if (current()) this.set({ pendingId: null });
    }
  }
  async export() {
    const selected = this.state.selected;
    if (!this.active || !selected || this.state.exporting) return;
    const generation = this.generation, selection = this.selection, requestId = this.id();
    const current = () => this.active && generation === this.generation && selection === this.selection && this.state.selected === selected;
    this.set({ exporting: true, error: '', message: 'Choose where to save the original report bytes…' });
    try {
      const result = await this.api.export(requestId, selected.summary.id, selected.summary.sha256);
      if (!current()) return;
      if (result.requestId !== requestId || result.reportId !== selected.summary.id || result.sourceSha256 !== selected.summary.sha256 || (result.file && (result.file.sha256 !== selected.summary.sha256 || result.file.sizeBytes !== selected.summary.sizeBytes))) throw new Error('Export receipt did not match the selected report bytes.');
      this.set({ message: result.file ? `Original report exported: ${result.file.name} · SHA-256 ${result.file.sha256}` : 'Export cancelled. The retained report remains selected.' });
    } catch (error) {
      if (current()) this.set({ error: errorText(error), message: 'Export failed. The retained report remains selected.' });
    } finally { this.set({ exporting: false }); }
  }
}
