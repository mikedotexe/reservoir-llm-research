import { describe, expect, it, vi } from 'vitest';
import { RecordingController, type ReaderApi } from './recordingController';
import { acceptedLessonReplacement } from './guideNavigation';
import type { FrameView, RecordSummary, VerificationReport } from './types';

const report: VerificationReport = { schema: 'test-report', status: 'passed', format: 'test', scope: 'Synthetic unit-test protocol', checkedSteps: 3, checkedTurns: 0, sha256: 'test-hash', modelsContacted: false, diagnostics: [] };
const record = (id: string): RecordSummary => ({ recordId: id, title: id, family: 'synthetic-test', format: 'test', origin: 'bundled', filename: 'test.json', sha256: 'test-hash', seed: '1', outcome: 'completed', verification: report,
  tracks: ['a', 'b'].map(id => ({ id, label: id, frameCount: 3, turnCount: 0, backend: null, model: null, timeline: [], timelineStride: 1 })) });
const frame = (index: number): FrameView => ({ index, step: String(index), time: index, state: Array(32).fill(0), input: [], noise: [], fillPercent: null, eigenvalues: null, retentionUsed: null, semanticTurnId: null });
function deferred<T>() { let resolve!: (value: T) => void; let reject!: (error: Error) => void; const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; }
function harness() {
  const api: ReaderApi = {
    openRecord: vi.fn(async (requestId, exampleId) => ({ requestId, cancelled: false, report, record: record(exampleId ?? 'external') })),
    recordFrame: vi.fn(async (requestId, recordId, trackId, index) => ({ requestId, recordId, trackId, frame: frame(index) })),
    recordTurn: vi.fn(), exportRecord: vi.fn(), closeRecord: vi.fn(async () => {}),
  };
  return { api, reader: new RecordingController(api) };
}

describe('accepted recording lifecycle', () => {
  it('does not mistake a preserved same-file guide handle for a successful retry', async () => {
    const { api, reader } = harness();
    await reader.open('lesson-original'); await reader.seek(2);
    const previousId = reader.snapshot().record?.recordId;
    vi.mocked(api.openRecord).mockRejectedValueOnce(new Error('fixture temporarily unavailable'));
    await reader.open('lesson-original');
    expect(acceptedLessonReplacement(previousId, reader.snapshot().record, 'test.json')).toBe(false);
    expect(reader.snapshot().frame?.index).toBe(2);
    expect(reader.snapshot().message).toContain('fixture temporarily unavailable');
    vi.mocked(api.openRecord).mockImplementationOnce(async requestId => ({ requestId, cancelled: true, report: null, record: null }));
    await reader.open('lesson-original');
    expect(acceptedLessonReplacement(previousId, reader.snapshot().record, 'test.json')).toBe(false);
    expect(reader.snapshot().frame?.index).toBe(2);
  });
  it('allows a newly accepted guide handle for the same file but rejects a different file', async () => {
    const { reader } = harness();
    await reader.open('lesson-original');
    const previousId = reader.snapshot().record?.recordId;
    await reader.open('lesson-new-handle');
    expect(acceptedLessonReplacement(previousId, reader.snapshot().record, 'test.json')).toBe(true);
    expect(acceptedLessonReplacement(previousId, reader.snapshot().record, 'another.json')).toBe(false);
    expect(acceptedLessonReplacement(previousId, null, 'test.json')).toBe(false);
  });
  it('adopts a new verified Library handle only after its first frame, without reopening a file', async () => {
    const { api, reader } = harness(); await reader.open('first');
    const library = record('library'); await reader.adopt(library);
    expect(reader.snapshot().record?.recordId).toBe('library');
    expect(api.openRecord).toHaveBeenCalledTimes(1);
    expect(api.closeRecord).toHaveBeenCalledWith('first');
    await reader.seek(2); await reader.adopt(library);
    expect(reader.snapshot().frame?.index).toBe(2);
    expect(api.closeRecord).not.toHaveBeenCalledWith('library');
  });
  it('rejects a failed adopted handle without replacing the current reading', async () => {
    const { api, reader } = harness(); await reader.open('first'); await reader.seek(1);
    await reader.adopt({ ...record('invalid'), verification: { ...report, status: 'incomplete' } });
    expect(reader.snapshot().record?.recordId).toBe('first');
    expect(reader.snapshot().frame?.index).toBe(1);
    expect(api.closeRecord).toHaveBeenCalledWith('invalid');
  });
  it('accepts a verified zero-frame recording without fetching a nonexistent frame', async () => {
    const { api, reader } = harness();
    const zero = record('zero'); zero.tracks = zero.tracks.map(track => ({ ...track, frameCount: 0 })); zero.outcome = 'cancelled';
    vi.mocked(api.openRecord).mockImplementationOnce(async requestId => ({ requestId, cancelled: false, report, record: zero }));
    await reader.open('zero');
    expect(reader.snapshot().record?.recordId).toBe('zero');
    expect(reader.snapshot().record?.outcome).toBe('cancelled');
    expect(reader.snapshot().frame).toBeNull();
    expect(api.recordFrame).not.toHaveBeenCalled();
    vi.mocked(api.exportRecord).mockImplementationOnce(async (requestId, recordId) => ({ requestId, recordId, file: { name: 'zero.json', sizeBytes: 10, sha256: 'test-hash' } }));
    await reader.export();
    expect(reader.snapshot().exported?.name).toBe('zero.json');
    await reader.close(); expect(api.closeRecord).toHaveBeenCalledWith('zero');
  });
  it('allows an empty track without losing another track’s reading position', async () => {
    const { api, reader } = harness();
    const mixed = record('mixed'); mixed.tracks[1].frameCount = 0;
    vi.mocked(api.openRecord).mockImplementationOnce(async requestId => ({ requestId, cancelled: false, report, record: mixed }));
    await reader.open('mixed'); await reader.seek(2); await reader.selectTrack('b');
    expect(reader.snapshot().trackId).toBe('b'); expect(reader.snapshot().frame).toBeNull();
    await reader.selectTrack('a'); expect(reader.snapshot().frame?.index).toBe(2);
  });
  it('retains the accepted record and cursor when verification is incomplete or cancelled', async () => {
    const { api, reader } = harness();
    await reader.open('first'); await reader.seek(2);
    vi.mocked(api.openRecord).mockImplementationOnce(async requestId => ({ requestId, cancelled: false, report: { ...report, status: 'incomplete', diagnostics: ['unsupported fixture'] }, record: null }));
    await reader.open('bad');
    expect(reader.snapshot().record?.recordId).toBe('first');
    expect(reader.snapshot().frame?.index).toBe(2);
    expect(reader.snapshot().report?.status).toBe('incomplete');
    vi.mocked(api.openRecord).mockImplementationOnce(async requestId => ({ requestId, cancelled: true, report: null, record: null }));
    await reader.open();
    expect(reader.snapshot().frame?.index).toBe(2);
    expect(api.closeRecord).not.toHaveBeenCalled();
  });
  it('keeps the prior reading until candidate initial-frame retrieval succeeds', async () => {
    const { api, reader } = harness();
    await reader.open('first'); await reader.seek(1);
    vi.mocked(api.recordFrame).mockRejectedValueOnce(new Error('frame unavailable'));
    await reader.open('candidate');
    expect(reader.snapshot().record?.recordId).toBe('first');
    expect(reader.snapshot().frame?.index).toBe(1);
    expect(api.closeRecord).toHaveBeenCalledWith('candidate');
    expect(api.closeRecord).not.toHaveBeenCalledWith('first');
  });
  it('ignores a slow obsolete open and releases its handle', async () => {
    const { api, reader } = harness();
    const slow = deferred<Awaited<ReturnType<ReaderApi['openRecord']>>>();
    let slowId = '';
    vi.mocked(api.openRecord).mockImplementationOnce(requestId => { slowId = requestId; return slow.promise; });
    const pending = reader.open('slow');
    await reader.open('latest');
    slow.resolve({ requestId: slowId, cancelled: false, report, record: record('slow') }); await pending;
    expect(reader.snapshot().record?.recordId).toBe('latest');
    expect(api.closeRecord).toHaveBeenCalledWith('slow');
  });
  it('ignores stale frame responses and preserves independent track cursors', async () => {
    const { api, reader } = harness(); await reader.open('first');
    const slow = deferred<Awaited<ReturnType<ReaderApi['recordFrame']>>>();
    let stale!: Awaited<ReturnType<ReaderApi['recordFrame']>>;
    vi.mocked(api.recordFrame).mockImplementationOnce((requestId, recordId, trackId, index) => { stale = { requestId, recordId, trackId, frame: frame(index) }; return slow.promise; });
    const pending = reader.seek(1); await reader.seek(2); slow.resolve(stale); await pending;
    expect(reader.snapshot().frame?.index).toBe(2);
    await reader.selectTrack('b'); await reader.seek(1); await reader.selectTrack('a');
    expect(reader.snapshot().frame?.index).toBe(2);
    expect(reader.snapshot().cursors).toEqual({ a: 2, b: 1 });
  });
  it('pauses on the final stored frame and retains the last frame after a read error', async () => {
    const { api, reader } = harness(); await reader.open('first'); reader.play();
    await reader.seek(2); expect(reader.snapshot().playing).toBe(false);
    vi.mocked(api.recordFrame).mockRejectedValueOnce(new Error('read failed')); await reader.seek(1);
    expect(reader.snapshot().frame?.index).toBe(2);
    expect(reader.snapshot().loadingFrame).toBe(false);
  });
  it('close invalidates pending work and a late open cannot resurrect the reader', async () => {
    const { api, reader } = harness(); await reader.open('first');
    const slow = deferred<Awaited<ReturnType<ReaderApi['openRecord']>>>(); let id = '';
    vi.mocked(api.openRecord).mockImplementationOnce(requestId => { id = requestId; return slow.promise; });
    const pending = reader.open('late'); await reader.close();
    slow.resolve({ requestId: id, cancelled: false, report, record: record('late') }); await pending;
    expect(reader.snapshot().record).toBeNull();
    expect(api.closeRecord).toHaveBeenCalledWith('first');
    expect(api.closeRecord).toHaveBeenCalledWith('late');
  });
});
