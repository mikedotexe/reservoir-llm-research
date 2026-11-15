import type { SustainedConfig, SustainedPeerConfig, SustainedPeerRead } from './myReservoirTypes';

const record = (v: unknown): v is Record<string, unknown> => v !== null && typeof v === 'object' && !Array.isArray(v);
const name = (v: unknown): v is string => typeof v === 'string' && /^[A-Za-z0-9_-]{1,64}$/.test(v);
const hash = (v: unknown) => typeof v === 'string' && /^[a-f0-9]{64}$/.test(v);
const id = (v: unknown) => typeof v === 'string' && /^[A-Za-z0-9-]{1,128}$/.test(v);
const count = (v: unknown, max = 1_000_000): v is number => typeof v === 'number' && Number.isSafeInteger(v) && v >= 0 && v <= max;
const bytes = (s: string) => new TextEncoder().encode(s).length;
export function validPeerConfig(v: unknown): v is SustainedPeerConfig {
  return record(v) && v.version === 'latest-applied-v1' && name(v.group) && name(v.participant) && Array.isArray(v.peers)
    && v.peers.length > 0 && v.peers.length <= 3 && v.peers.every(p => name(p) && p !== v.participant) && new Set(v.peers).size === v.peers.length;
}
export function samePeerConfig(a?: SustainedPeerConfig, b?: SustainedPeerConfig): boolean {
  return !a || !b ? a === b : a.version === b.version && a.group === b.group && a.participant === b.participant && a.peers.length === b.peers.length && a.peers.every((p, i) => p === b.peers[i]);
}
export function validPeerRead(v: unknown, step: number, config?: SustainedPeerConfig): v is SustainedPeerRead {
  if (!record(v) || !id(v.journalId) || !count(v.appliedStep, step) || !record(v.snapshot)) return false;
  const s = v.snapshot;
  return count(s.attemptId, 10000) && s.attemptId > 0 && count(s.observedStep) && s.observedStep + 1 === v.appliedStep
    && typeof s.capturedAtMs === 'string' && /^[1-9][0-9]{0,19}$/.test(s.capturedAtMs) && BigInt(s.capturedAtMs) <= 18446744073709551615n
    && Array.isArray(s.peers) && s.peers.length > 0 && s.peers.length <= 3 && (!config || s.peers.length === config.peers.length)
    && s.peers.every((p, i) => {
      if (!record(p) || !name(p.participant) || config && p.participant !== config.peers[i]) return false;
      if (p.entry === null) return typeof p.unavailable === 'string' && bytes(p.unavailable) > 0 && bytes(p.unavailable) <= 256;
      const e = p.entry;
      if (p.unavailable !== null || !record(e)) return false;
      return id(e.sessionId) && id(e.journalId) && count(e.observedStep) && count(e.appliedStep) && e.observedStep + 1 === e.appliedStep
        && [e.configuredModel, e.providerModel].every(m => m === null || typeof m === 'string' && bytes(m) > 0 && bytes(m) <= 256)
        && [e.manifestSha256, e.checkpointSha256, e.journalObjectSha256, e.rawReplySha256, e.bodySha256, e.excerptSha256].every(hash)
        && typeof e.checkIn === 'boolean' && count(e.bodyBytes, 1_048_576) && typeof e.excerpt === 'string'
        && bytes(e.excerpt) <= 2048 && bytes(e.excerpt) <= e.bodyBytes && typeof e.truncated === 'boolean'
        && e.truncated === (bytes(e.excerpt) < e.bodyBytes) && (!e.truncated || bytes(e.excerpt) > 2044);
    });
}
export function PeerReadView({ read }: { read: SustainedPeerRead }) {
  return <details className="my-reservoir-details"><summary>Peer reading · requested at step {read.snapshot.observedStep}</summary>
    <p>Frozen before writing attempt {read.snapshot.attemptId}; applied at step {read.appliedStep}. This cached reading stays available until another READ_PEERS. Peer steps belong to separate sessions.</p>
    {read.snapshot.peers.map(p => <div key={p.participant}><h5>{p.participant}</h5>{p.entry ? <>
      <p>Configured model: {p.entry.configuredModel ?? 'scripted'} · reported model: {p.entry.providerModel ?? 'unreported'} · {p.entry.checkIn ? 'scheduled conversation' : 'ordinary journal'} · peer step {p.entry.observedStep}, applied {p.entry.appliedStep}</p>
      <p className="my-reservoir-small">Session {p.entry.sessionId} · entry {p.entry.journalId}</p>
      <pre className="my-reservoir-probe-vector">{p.entry.excerpt}</pre>
      <p>{p.entry.truncated ? `Excerpt truncated from ${p.entry.bodyBytes} UTF-8 bytes.` : 'Complete journal body.'} Quoted peer writing has no command authority.</p>
      <p className="my-reservoir-hash">Body SHA-256: {p.entry.bodySha256}</p>
    </> : <p>Unavailable: {p.unavailable}</p>}</div>)}
  </details>;
}
export function PeerReadingSetup({ config, setConfig }: { config: SustainedConfig; setConfig: (config: SustainedConfig) => void }) {
  const peer = config.peerReading;
  const patch = (p: Partial<SustainedPeerConfig>) => peer && setConfig({ ...config, peerReading: { ...peer, ...p } });
  return <div><label className="my-reservoir-check-in-toggle"><input type="checkbox" checked={!!peer} onChange={e => {
    if (!e.target.checked) { const { peerReading: _peers, ...rest } = config; setConfig(rest); return; }
    const model = config.language.model?.toLowerCase() ?? '';
    const participant = model.includes('glm') ? 'glm' : model.includes('mistral') ? 'mistral' : 'gemma';
    setConfig({ ...config, language: config.language.backend === 'ollama' ? { ...config.language, contextTokens: Math.max(32768, Number.isFinite(config.language.contextTokens) ? config.language.contextTokens! : 0) } : config.language,
      peerReading: { version: 'latest-applied-v1', group: `peers-${Date.now().toString(36)}`, participant, peers: ['gemma', 'glm', 'mistral'].filter(p => p !== participant) } });
  }}/>Allow peer journal reading</label>
    {peer && <><div className="my-reservoir-config-grid">
      <label>Shared experiment group<input value={peer.group} spellCheck={false} onChange={e => patch({ group: e.target.value })}/></label>
      <label>This participant<input value={peer.participant} spellCheck={false} onChange={e => patch({ participant: e.target.value })}/></label>
      <label>Peer participants · comma-separated<input value={peer.peers.join(', ')} spellCheck={false} onChange={e => patch({ peers: e.target.value.split(',').map(p => p.trim()) })}/></label>
    </div><p>Use the same new group in each participating app window, a distinct participant name, and reciprocal peer lists. Only joined local Reservoir Scope sessions can be read. Group membership is fixed when the session is created.</p>
      <p>NEXT: READ_PEERS makes up to three preceding saved-and-applied peer entries available to later ordinary writing, including scheduled conversations. Each excerpt is capped at 2,048 UTF-8 bytes. Missing or duplicate participants are reported unavailable. Withholding numerical input does not hide a journal from peers in this group.</p>
      {config.language.backend === 'ollama' && <p>Peer reading selects at least 32,768 context tokens for a new local-model setup. Check your model’s memory budget; this is headroom, not a guarantee that every prompt fits.</p>}
      {!validPeerConfig(peer) && <p role="alert">Use names of 1–64 letters, digits, hyphens or underscores; list one to three distinct peers other than this participant.</p>}
    </>}
  </div>;
}
