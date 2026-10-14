import { invoke, isTauri } from '@tauri-apps/api/core';
import { errorText } from './api';
import type { LanguageConfiguration } from './freshTypes';

export interface ModelReadinessResult {
  requestId: string; operationId: string; endpoint: string; requestedModel: string; status: 'found' | 'unavailable' | 'cancelled';
  matchedModel: string | null; digest: string | null; checkedAtMs: string; diagnostic: string | null;
}
export interface ModelReadinessApi { check(requestId: string, configuration: LanguageConfiguration): Promise<ModelReadinessResult>; cancel(requestId: string): Promise<void> }
const readinessApi: ModelReadinessApi = {
  check: (requestId, configuration) => { if (!isTauri()) return Promise.reject(new Error('Open the desktop app to explicitly check a local model.')); return invoke('check_local_model', { requestId, configuration }); },
  cancel: requestId => { if (!isTauri()) return Promise.resolve(); return invoke('cancel_local_model_check', { requestId }); },
};
export const languageKey = (c: LanguageConfiguration) => JSON.stringify([c.backend, c.endpoint ?? null, c.model ?? null, c.contextTokens ?? null, c.responseFormat ?? null]);
/** Mirrors the transport boundary for immediate form feedback; Rust remains authoritative. */
export function localModelError(c: LanguageConfiguration): string | null {
  if (c.backend !== 'ollama') return 'Select a local Ollama backend to check it.';
  const endpoint = c.endpoint ?? '', match = /^http:\/\/(localhost|127\.0\.0\.1|\[::1\]):([0-9]+)\/?$/.exec(endpoint);
  if (!match || !Number.isInteger(Number(match[2])) || Number(match[2]) < 1 || Number(match[2]) > 65535) return 'Enter an explicit HTTP loopback endpoint with a port, without credentials, path, query or fragment.';
  if (!c.model || c.model !== c.model.trim() || new TextEncoder().encode(c.model).length > 256) return 'Enter an exact model name, at most 256 UTF-8 bytes, without surrounding spaces.';
  if (!Number.isInteger(c.contextTokens) || c.contextTokens! < 512 || c.contextTokens! > 32768) return 'Context must be an integer from 512 to 32768 tokens.';
  return null;
}
export interface ModelReadinessState { key: string; checking: boolean; result: ModelReadinessResult | null; error: string; message: string }
let serial = 0;
export class LocalModelController {
  private state: ModelReadinessState = { key: '', checking: false, result: null, error: '', message: '' };
  private listeners = new Set<() => void>(); private epoch = 0; private request: string | null = null;
  constructor(private api: ModelReadinessApi = readinessApi) {}
  snapshot = () => this.state;
  subscribe = (fn: () => void) => { this.listeners.add(fn); return () => { this.listeners.delete(fn); }; };
  private set(patch: Partial<ModelReadinessState>) { this.state = { ...this.state, ...patch }; this.listeners.forEach(fn => fn()); }
  select(c: LanguageConfiguration) {
    const key = languageKey(c); if (this.state.key === key) return;
    this.epoch++; const request = this.request; this.request = null;
    this.set({ key, checking: false, result: null, error: '', message: '' });
    if (request) void this.api.cancel(request).catch(() => {});
  }
  async check(c: LanguageConfiguration) {
    this.select(c); if (this.state.checking) return;
    const error = localModelError(c); if (error) { this.set({ error, result: null }); return; }
    const epoch = ++this.epoch, requestId = `model-readiness-${Date.now()}-${++serial}`, key = languageKey(c);
    this.request = requestId; this.set({ checking: true, error: '', result: null, message: 'Checking this explicit endpoint and model…' });
    try {
      const result = await this.api.check(requestId, { ...c });
      if (epoch !== this.epoch || key !== this.state.key || this.request !== requestId) return;
      if (result.requestId !== requestId || !result.operationId || result.endpoint !== c.endpoint || result.requestedModel !== c.model || !['found', 'unavailable', 'cancelled'].includes(result.status) || !/^[0-9]+$/.test(result.checkedAtMs) || (result.status === 'found' && !result.matchedModel)) throw new Error('Readiness response does not match the selected endpoint and model.');
      this.set({ result, message: '', error: '' });
    } catch (error) { if (epoch === this.epoch) this.set({ error: errorText(error), message: '' }); }
    finally { if (epoch === this.epoch) { this.request = null; this.set({ checking: false }); } }
  }
  async cancel() {
    const request = this.request, epoch = ++this.epoch; this.request = null;
    this.set({ checking: false, result: null, error: '', message: 'Readiness result discarded. Cancellation requested; no experiment was started.' });
    if (request) try { await this.api.cancel(request); } catch (error) { if (epoch === this.epoch) this.set({ error: `Cancellation could not be confirmed: ${errorText(error)}. Any late result remains discarded.` }); }
  }
  dispose() { this.epoch++; const request = this.request; this.request = null; if (request) void this.api.cancel(request).catch(() => {}); }
}
