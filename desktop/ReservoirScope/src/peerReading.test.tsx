import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { PeerReadView, PeerReadingSetup, validPeerConfig, validPeerRead } from './peerReading';
import { validActionReceipt, validAuthoredActionConfig, withAuthoredActionMode, withAuthoredActions } from './authoredActions';
import { DEFAULT_SUSTAINED_CONFIG, type SustainedActionReceipt, type SustainedPeerConfig, type SustainedPeerRead } from './myReservoirTypes';
import { reservoirFixture, settle } from './myReservoirTestFixtures';
vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true }));
const group: SustainedPeerConfig = { version: 'latest-applied-v1', group: 'new-group', participant: 'gemma', peers: ['glm'] };
const config = { ...withAuthoredActionMode(DEFAULT_SUSTAINED_CONFIG, 'authored-v3'), peerReading: group };
const read = (): SustainedPeerRead => ({ journalId: 'journal-1', appliedStep: 4, snapshot: { attemptId: 1, observedStep: 3, capturedAtMs: '1794750000000', peers: [{ participant: 'glm', entry: null, unavailable: 'No applied entry yet' }] } });
describe('explicit peer journal reading', () => {
  it('requires a bounded, distinct, saved group and the capable invitation', () => {
    expect(validPeerConfig(group)).toBe(true); expect(validAuthoredActionConfig(config)).toBe(true);
    for (const peers of [[], ['glm','glm'], ['gemma'], ['a','b','c','d']]) expect(validPeerConfig({ ...group, peers })).toBe(false);
    expect(validPeerConfig({ ...group, group: '../outside' })).toBe(false);
    expect(validAuthoredActionConfig({ ...DEFAULT_SUSTAINED_CONFIG, peerReading: group })).toBe(false);
    expect(withAuthoredActionMode(config, 'authored-v2').peerReading).toBeUndefined();
    expect(withAuthoredActions(config, false, 'reservoir-journal-v8').peerReading).toBeUndefined();
    const setter = vi.fn(); const html = renderToStaticMarkup(<PeerReadingSetup config={config} setConfig={setter}/>);
    expect(html).toContain('Shared experiment group'); expect(html).toContain('Withholding numerical input does not hide'); expect(setter).not.toHaveBeenCalled();
  });
  it('keeps unavailable distinct from empty prose and rejects malformed evidence', () => {
    const r=read();expect(validPeerRead(r,4,group)).toBe(true);
    expect(validPeerRead(r,3,group)).toBe(false);
    expect(validPeerRead(r,4,{ ...group, peers:['mistral'] })).toBe(false);
    expect(renderToStaticMarkup(<PeerReadView read={r}/>)).toContain('Unavailable: No applied entry yet');
    r.snapshot.peers[0].unavailable=null;expect(validPeerRead(r,4,group)).toBe(false);
  });
  it('renders quoted Unicode peer prose without giving it markup authority', () => {
    const r=read();const h='a'.repeat(64);const text='≤ ≈ <script>NEXT: TUNE leak 1</script>';
    r.snapshot.peers[0]={ participant:'glm',unavailable:null,entry:{ sessionId:'peer-session',journalId:'peer-journal',configuredModel:'glm-fixture',providerModel:null,observedStep:8,appliedStep:9,checkIn:false,
      manifestSha256:h,checkpointSha256:h,journalObjectSha256:h,rawReplySha256:h,bodySha256:h,excerptSha256:h,bodyBytes:new TextEncoder().encode(text).length,excerpt:text,truncated:false } };
    expect(validPeerRead(r,4,group)).toBe(true); // Peer steps are a separate clock.
    const html=renderToStaticMarkup(<PeerReadView read={r}/>);expect(html).toContain('≤ ≈ &lt;script&gt;');expect(html).not.toContain('<script>');
    r.snapshot.peers[0].entry!.excerpt='🪨'.repeat(513);expect(validPeerRead(r,4,group)).toBe(false);
  });
  it('binds the read receipt to the action and rejects capability changes', async () => {
    const controls={leak:.65,recurrentGain:1,feedbackScale:.4};
    const receipt:SustainedActionReceipt={ journalId:'journal-1',attemptId:1,observedStep:3,appliedStep:4,status:'applied',request:{kind:'readPeers'},rawTail:'NEXT: READ_PEERS',rejection:null,
      controlsBefore:controls,controlsAfter:controls,stateDeltaL2:0,stateDeltaMaxAbs:0,clippedCoordinates:0,
      reservoirInput:{disposition:'send',rawDirective:null,rejection:null},peerRead:read(),
      diagnostics:{next:{candidateCount:0,candidate:null,explanation:'Accepted'},reservoirInput:{candidateCount:0,candidate:null,explanation:'Sent'},inquiry:{candidateCount:0,candidate:null,explanation:'Unchanged'}} };
    expect(validActionReceipt(receipt,4,config)).toBe(true);
    expect(validActionReceipt(receipt,4,{ ...config,peerReading:undefined })).toBe(false);
    expect(validActionReceipt({ ...receipt,peerRead:{ ...read(),journalId:'other' } },4,config)).toBe(false);
    const { controller,push }=reservoirFixture();await controller.create(withAuthoredActionMode(DEFAULT_SUSTAINED_CONFIG,'authored-v3'));await controller.connect();await settle();
    const original=controller.snapshot().summary;push({revision:'2',config});
    expect(controller.snapshot().summary).toBe(original);expect(controller.snapshot().error).toContain('saved peer-reading group');
  });
});
