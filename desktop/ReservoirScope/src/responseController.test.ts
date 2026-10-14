import { describe, expect, it, vi } from 'vitest';
import { ResponseController } from './responseController';
import type { ResponseApi, ResponseEventDetail, ResponseEventResult, ResponseExportResult, ResponseFrame, ResponseFrameResult, ResponseOpenResult, ResponseSource, ResponseSummary } from './responseTypes';

const vec = (first = 0) => [first, ...Array<number>(127).fill(0)];
function summary(responseId: string, source: ResponseSource = 'native-example'): ResponseSummary {
  const native = source !== 'simulation-example';
  return { responseId, kind: native ? 'native' : 'simulation', origin: source === 'native-file' ? 'openedFile' : 'bundled', filename: 'test.json', sha256: 'a'.repeat(64), sizeBytes: 1234, frameCount: 4, nodeCount: 128, fixedDeltaScale: native ? 0.125 : 0.001, firstLabel: native ? 'Ordinary step' : 'Control', secondLabel: native ? 'Applied result' : 'Perturbed', returnThreshold: native ? null : 0.0001, provenance: ['Synthetic protocol fixture'], missingness: ['No time or fill'], metadata: {}, timeline: Array.from({ length: 4 }, (_, index) => ({ index, position: String(200 + index), l2: index / 100, receiptIndex: native ? index : null })), events: native ? Array.from({ length: 4 }, (_, index) => ({ index, status: 'applied', frameIndex: index, isBoundary: true })) : [] };
}
function frame(index: number): ResponseFrame { return { index, position: String(200 + index), first: vec(), second: vec(index / 100), delta: vec(index / 100), l2: index / 100, direction: vec(1), realizedNoise: vec(), metadata: { Step: String(200 + index) } }; }
function event(index: number): ResponseEventDetail { const f = frame(index); return { index, status: 'applied', hasState: true, isBoundary: true, metadata: { Step: f.position }, direction: f.direction!, realizedNoise: f.realizedNoise, first: f.first, second: f.second, delta: f.delta }; }
function deferred<T>() { let resolve!: (value: T) => void; let reject!: (error: Error) => void; const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; }
function harness() {
  let handle = 0;
  const api: ResponseApi = {
    open: vi.fn(async (requestId, source) => ({ requestId, cancelled: false, response: summary(`response-${++handle}`, source) })),
    frame: vi.fn(async (requestId, responseId, index) => ({ requestId, responseId, frame: frame(index) })),
    event: vi.fn(async (requestId, responseId, index) => ({ requestId, responseId, event: event(index) })),
    export: vi.fn(async (requestId, responseId) => ({ requestId, responseId, file: { name: 'export.json', sizeBytes: 1234, sha256: 'a'.repeat(64) } })),
    close: vi.fn(async () => {}),
  };
  return { api, controller: new ResponseController(api) };
}

describe('atomic response evidence replacement', () => {
  it('preserves accepted handle, selected frame and coordinate on cancellation or invalid evidence', async () => {
    const { api, controller } = harness(); await controller.open('native-example'); await controller.frame(2); controller.selectNode(127); const accepted = controller.snapshot();
    vi.mocked(api.open).mockImplementationOnce(async requestId => ({ requestId, cancelled: true, response: null })); await controller.open('native-file');
    expect(controller.snapshot().summary).toBe(accepted.summary); expect(controller.snapshot().frame).toBe(accepted.frame); expect(controller.snapshot().node).toBe(127);
    vi.mocked(api.open).mockRejectedValueOnce(new Error('changed native boundary')); await controller.open('native-file');
    expect(controller.snapshot().summary).toBe(accepted.summary); expect(controller.snapshot().frame).toBe(accepted.frame); expect(api.close).not.toHaveBeenCalled();
    expect(api.open).toHaveBeenLastCalledWith(expect.any(String), 'native-file', accepted.summary!.responseId);
  });
  it('does not replace accepted data until the candidate first frame is readable', async () => {
    const { api, controller } = harness(); await controller.open('native-example'); const accepted = controller.snapshot(); const slow = deferred<ResponseFrameResult>(); let result!: ResponseFrameResult;
    vi.mocked(api.frame).mockImplementationOnce((requestId, responseId, index) => { result = { requestId, responseId, frame: frame(index) }; return slow.promise; });
    const opening = controller.open('simulation-example'); await vi.waitFor(() => expect(api.frame).toHaveBeenCalledTimes(2));
    expect(controller.snapshot().summary).toBe(accepted.summary); expect(api.close).not.toHaveBeenCalled();
    slow.resolve(result); await opening; expect(controller.snapshot().summary?.kind).toBe('simulation'); expect(api.close).toHaveBeenCalledWith(accepted.summary!.responseId);
  });
  it('releases a candidate whose first frame fails and retains the previous selection', async () => {
    const { api, controller } = harness(); await controller.open('native-example'); await controller.frame(3); const accepted = controller.snapshot();
    vi.mocked(api.frame).mockRejectedValueOnce(new Error('frame unavailable')); await controller.open('simulation-example');
    expect(controller.snapshot().summary).toBe(accepted.summary); expect(controller.snapshot().frame).toBe(accepted.frame); expect(controller.snapshot().opening).toBe(false); expect(api.close).toHaveBeenCalledWith('response-2'); expect(api.close).not.toHaveBeenCalledWith('response-1');
  });
  it('releases obsolete opens and does not resurrect a closed response', async () => {
    const { api, controller } = harness(); const slow = deferred<ResponseOpenResult>(); let request = '';
    vi.mocked(api.open).mockImplementationOnce(requestId => { request = requestId; return slow.promise; }); const pending = controller.open('native-file'); await controller.open('simulation-example');
    slow.resolve({ requestId: request, cancelled: false, response: summary('obsolete', 'native-file') }); await pending;
    expect(controller.snapshot().summary?.kind).toBe('simulation'); expect(api.close).toHaveBeenCalledWith('obsolete');
    const closed = deferred<ResponseOpenResult>(); vi.mocked(api.open).mockImplementationOnce(requestId => { request = requestId; return closed.promise; }); const late = controller.open('native-example'); await controller.close();
    closed.resolve({ requestId: request, cancelled: false, response: summary('late') }); await late; expect(controller.snapshot().summary).toBeNull(); expect(api.close).toHaveBeenCalledWith('late');
  });
  it('discards a candidate first-frame result after close', async () => {
    const { api, controller } = harness(); const slow = deferred<ResponseFrameResult>(); let result!: ResponseFrameResult;
    vi.mocked(api.frame).mockImplementationOnce((requestId, responseId, index) => { result = { requestId, responseId, frame: frame(index) }; return slow.promise; }); const pending = controller.open('native-example');
    await vi.waitFor(() => expect(api.frame).toHaveBeenCalledTimes(1)); await controller.close(); slow.resolve(result); await pending;
    expect(controller.snapshot().frame).toBeNull(); expect(api.close).toHaveBeenCalledWith('response-1');
  });
  it('accepts an event-only bundle without inventing an applied frame', async () => {
    const { api, controller } = harness(); vi.mocked(api.open).mockImplementationOnce(async requestId => ({ requestId, cancelled: false, response: { ...summary('events'), frameCount: 0, timeline: [], events: [{ index: 0, status: 'accepted', frameIndex: null, isBoundary: false }] } }));
    await controller.open('native-example'); expect(controller.snapshot().summary?.responseId).toBe('events'); expect(controller.snapshot().frame).toBeNull(); expect(api.frame).not.toHaveBeenCalled(); controller.play(0); expect(controller.snapshot().playing).toBe(false);
  });
  it('late previous-handle cleanup cannot reset a newer selection', async () => {
    const { api, controller } = harness(); await controller.open('native-example'); const close = deferred<void>(); vi.mocked(api.close).mockImplementationOnce(() => close.promise);
    const reload = controller.open('native-example'); await vi.waitFor(() => expect(controller.snapshot().summary?.responseId).toBe('response-2')); await controller.frame(2); controller.selectNode(11); close.resolve(); await reload;
    expect(controller.snapshot().frame?.index).toBe(2); expect(controller.snapshot().node).toBe(11);
  });
  it.each(['source', 'origin', 'dimensions', 'coverage', 'position', 'scale', 'request'] as const)('rejects a mismatched %s open before replacing evidence', async flaw => {
    const { api, controller } = harness(); await controller.open('native-example'); const accepted = controller.snapshot().summary;
    vi.mocked(api.open).mockImplementationOnce(async requestId => { const candidate = summary('bad');
      switch (flaw) { case 'source': candidate.kind = 'simulation'; break; case 'origin': candidate.origin = 'openedFile'; break; case 'dimensions': candidate.nodeCount = 32; break; case 'coverage': candidate.timeline.pop(); break; case 'position': candidate.timeline[0].position = 'rounded ID'; break; case 'scale': candidate.fixedDeltaScale = 0; break; }
      return { requestId: flaw === 'request' ? 'other' : requestId, cancelled: false, response: candidate };
    }); await controller.open('native-example'); expect(controller.snapshot().summary).toBe(accepted); expect(api.close).toHaveBeenCalledWith('bad');
  });
});

describe('response frame and event generations', () => {
  it('ignores stale frame success across a later read and close', async () => {
    const { api, controller } = harness(); await controller.open('native-example'); const slow = deferred<ResponseFrameResult>(); let result!: ResponseFrameResult;
    vi.mocked(api.frame).mockImplementationOnce((requestId, responseId, index) => { result = { requestId, responseId, frame: frame(index) }; return slow.promise; }); const pending = controller.frame(1); await controller.frame(3); slow.resolve(result); await pending; expect(controller.snapshot().frame?.index).toBe(3);
    const late = deferred<ResponseFrameResult>(); vi.mocked(api.frame).mockImplementationOnce((requestId, responseId, index) => { result = { requestId, responseId, frame: frame(index) }; return late.promise; }); const closing = controller.frame(2); await controller.close(); late.resolve(result); await closing; expect(controller.snapshot().frame).toBeNull();
  });
  it.each(['request', 'handle', 'index', 'position', 'l2', 'vector', 'nonfinite'] as const)('retains the selected frame after malformed %s reply', async flaw => {
    const { api, controller } = harness(); await controller.open('native-example'); const accepted = controller.snapshot().frame;
    vi.mocked(api.frame).mockImplementationOnce(async (requestId, responseId, index) => { const value = frame(index); switch (flaw) { case 'index': value.index = 0; break; case 'position': value.position = '999'; break; case 'l2': value.l2 = 1; break; case 'vector': value.delta.pop(); break; case 'nonfinite': value.first[0] = NaN; break; } return { requestId: flaw === 'request' ? 'bad' : requestId, responseId: flaw === 'handle' ? 'bad' : responseId, frame: value }; });
    await controller.frame(2); expect(controller.snapshot().frame).toBe(accepted); expect(controller.snapshot().loading).toBe(false); expect(controller.snapshot().message).toContain('retained');
  });
  it('event selection never changes playback frame and discards stale event reads', async () => {
    const { api, controller } = harness(); await controller.open('native-example'); await controller.frame(2); const accepted = controller.snapshot().frame; const slow = deferred<ResponseEventResult>(); let result!: ResponseEventResult;
    vi.mocked(api.event).mockImplementationOnce((requestId, responseId, index) => { result = { requestId, responseId, event: event(index) }; return slow.promise; }); const pending = controller.selectEvent(0); await controller.selectEvent(3); slow.resolve(result); await pending;
    expect(controller.snapshot().event?.index).toBe(3); expect(controller.snapshot().frame).toBe(accepted);
    const failed = deferred<ResponseEventResult>(); vi.mocked(api.event).mockImplementationOnce(() => failed.promise); const old = controller.selectEvent(1); await controller.open('simulation-example'); failed.reject(new Error('stale receipt')); await old;
    expect(controller.snapshot().event).toBeNull(); expect(controller.snapshot().message).not.toContain('stale receipt');
  });
  it('rejects invalid coordinate and event selections without an IPC call', async () => {
    const { api, controller } = harness(); await controller.open('native-example'); controller.selectNode(127); for (const node of [-1, 128, 0.5, NaN]) controller.selectNode(node);
    for (const index of [-1, 4, 0.5]) await controller.selectEvent(index); expect(controller.snapshot().node).toBe(127); expect(api.event).not.toHaveBeenCalled();
  });
});

describe('response raw-boundary playback', () => {
  it('holds exact frames between monotonic ordinal boundaries without repeating IPC', async () => {
    const { api, controller } = harness(); await controller.open('native-example'); const original = controller.snapshot().frame; controller.play(1000); await controller.tick(1100);
    expect(controller.snapshot().frame).toBe(original); expect(api.frame).toHaveBeenCalledTimes(1); await controller.tick(1500); expect(controller.snapshot().frame?.index).toBe(1);
    await controller.tick(1400); expect(api.frame).toHaveBeenCalledTimes(2); await controller.tick(2000); expect(controller.snapshot().frame?.index).toBe(3); expect(controller.snapshot().playing).toBe(false);
  });
  it('pause/navigation invalidates an in-flight playback frame', async () => {
    const { api, controller } = harness(); await controller.open('native-example'); const slow = deferred<ResponseFrameResult>(); let result!: ResponseFrameResult;
    vi.mocked(api.frame).mockImplementationOnce((requestId, responseId, index) => { result = { requestId, responseId, frame: frame(index) }; return slow.promise; }); controller.play(0); const pending = controller.tick(500); controller.pause(); slow.resolve(result); await pending;
    expect(controller.snapshot().frame?.index).toBe(0); expect(controller.snapshot().playing).toBe(false); expect(controller.snapshot().loading).toBe(false);
  });
  it('manual seeking supersedes playback; loading prevents a new playback clock', async () => {
    const { api, controller } = harness(); await controller.open('native-example'); const slow = deferred<ResponseFrameResult>(); let result!: ResponseFrameResult;
    vi.mocked(api.frame).mockImplementationOnce((requestId, responseId, index) => { result = { requestId, responseId, frame: frame(index) }; return slow.promise; }); controller.play(0); const pending = controller.tick(500); await controller.frame(2); slow.resolve(result); await pending; expect(controller.snapshot().frame?.index).toBe(2);
    const loading = deferred<ResponseFrameResult>(); vi.mocked(api.frame).mockImplementationOnce((requestId, responseId, index) => { result = { requestId, responseId, frame: frame(index) }; return loading.promise; }); const manual = controller.frame(0); controller.play(2000); expect(controller.snapshot().playing).toBe(false); loading.resolve(result); await manual;
  });
  it('accumulates elapsed time while allowing only one pending playback read', async () => {
    const { api, controller } = harness(); await controller.open('native-example'); const slow = deferred<ResponseFrameResult>(); let result!: ResponseFrameResult;
    vi.mocked(api.frame).mockImplementationOnce((requestId, responseId, index) => { result = { requestId, responseId, frame: frame(index) }; return slow.promise; }); controller.setRate(1); controller.play(0); const pending = controller.tick(1100); await controller.tick(2500); expect(api.frame).toHaveBeenCalledTimes(2); slow.resolve(result); await pending; await controller.tick(2500); expect(controller.snapshot().frame?.index).toBe(2);
  });
});

describe('response original-byte export', () => {
  it('accepts only an exact original byte identity and keeps previous receipt on cancellation', async () => {
    const { api, controller } = harness(); await controller.open('native-example'); await controller.export(); const exported = controller.snapshot().exported; expect(exported?.sha256).toBe('a'.repeat(64));
    vi.mocked(api.export).mockImplementationOnce(async (requestId, responseId) => ({ requestId, responseId, file: null })); await controller.export(); expect(controller.snapshot().exported).toBe(exported);
    vi.mocked(api.export).mockImplementationOnce(async (requestId, responseId) => ({ requestId, responseId, file: { name: 'wrong.json', sizeBytes: 1235, sha256: 'b'.repeat(64) } })); await controller.export(); expect(controller.snapshot().exported).toBe(exported); expect(controller.snapshot().message).toContain('did not match');
  });
  it('ignores an export response after explicit close', async () => {
    const { api, controller } = harness(); await controller.open('native-example'); const slow = deferred<ResponseExportResult>(); let result!: ResponseExportResult;
    vi.mocked(api.export).mockImplementationOnce((requestId, responseId) => { result = { requestId, responseId, file: { name: 'original.json', sizeBytes: 1234, sha256: 'a'.repeat(64) } }; return slow.promise; }); const pending = controller.export(); await controller.close(); slow.resolve(result); await pending; expect(controller.snapshot().summary).toBeNull(); expect(controller.snapshot().exported).toBeNull(); expect(controller.snapshot().message).toBe('');
  });
});
