import { describe, expect, it, vi } from 'vitest';
import { PreparationController } from './preparationController';
import type { PreparationApi, PreparationReport, PreparationReportSummary, PreparationReportResult, PreparationExportResult, PreparationHistoryResult } from './preparationTypes';

const original: PreparationReportSummary = { id: 'original', kind: 'original', title: 'Original', status: 'unavailable', filename: 'original.json', sha256: 'a'.repeat(64), sizeBytes: 10, summary: 'Connection refused' };
const retry: PreparationReportSummary = { ...original, id: 'retry', kind: 'retry', title: 'Later retry', status: 'failed', filename: 'retry.json', sha256: 'b'.repeat(64) };
const report = (status: string): PreparationReport => ({ schema: 'report-v1', status, scope: null, inspectionScope: 'Historical metadata only', sections: [], attempts: [] });
function fixture() {
  const api: PreparationApi = {
    list: async requestId => ({ requestId, reports: [original, retry], examples: [] }),
    get: async (requestId, reportId) => ({ requestId, reportId, sha256: reportId === 'original' ? original.sha256 : retry.sha256, report: report(reportId === 'original' ? 'unavailable' : 'failed'), retainedExampleId: reportId === 'retry' ? 'example-model-observation-active' : null, retainedExampleDiagnostic: null }),
    export: async (requestId, reportId, sourceSha256) => ({ requestId, reportId, sourceSha256, file: null }),
  };
  return { api, controller: new PreparationController(api) };
}
async function activate(controller: PreparationController) {
  controller.activate(true);
  await vi.waitFor(() => expect(controller.snapshot().busy).toBe(false));
}
describe('retained preparation history lifecycle', () => {
  it('does no read while inactive and keeps the unavailable outcome after activation', async () => {
    const { api, controller } = fixture(); const list = vi.spyOn(api, 'list');
    await controller.refresh(); await controller.select(original); await controller.export(); expect(list).not.toHaveBeenCalled();
    await activate(controller); expect(list).toHaveBeenCalledOnce(); expect(controller.snapshot().selected?.report.status).toBe('unavailable');
    controller.activate(false); await activate(controller); expect(list).toHaveBeenCalledOnce();
  });
  it('keeps the selected retry across navigation without rereading or reopening history', async () => {
    const { api, controller } = fixture();
    const list = vi.spyOn(api, 'list'), get = vi.spyOn(api, 'get'), exported = vi.spyOn(api, 'export');
    await activate(controller); await controller.select(retry);
    const accepted = controller.snapshot().selected;
    expect(accepted?.summary.id).toBe('retry');
    expect(accepted?.retainedExampleId).toBe('example-model-observation-active');
    list.mockClear(); get.mockClear();
    controller.activate(false);
    await controller.refresh(); await controller.select(original);
    await activate(controller); controller.activate(true);
    expect(controller.snapshot().selected).toBe(accepted);
    expect(controller.snapshot().selected?.report.status).toBe('failed');
    expect(controller.snapshot().pendingId).toBeNull();
    expect(list).not.toHaveBeenCalled(); expect(get).not.toHaveBeenCalled();
    expect(exported).not.toHaveBeenCalled();
  });
  it('retains accepted reading when refresh or a new detail request fails', async () => {
    const { api, controller } = fixture(); await activate(controller); const selected = controller.snapshot().selected;
    api.list = async () => { throw new Error('Package hash changed'); }; await controller.refresh();
    expect(controller.snapshot().selected).toBe(selected); expect(controller.snapshot().error).toBe('Package hash changed');
    api.get = async () => { throw new Error('Report missing'); }; await controller.select(retry);
    expect(controller.snapshot().selected).toBe(selected); expect(controller.snapshot().error).toBe('Report missing'); expect(controller.snapshot().pendingId).toBeNull();
  });
  it.each([false, true])('ignores a late detail response/failure after another selection (failure=%s)', async failure => {
    const { api, controller } = fixture(); await activate(controller); const get = api.get; let finish!: () => void;
    api.get = (requestId, reportId) => new Promise((resolve, reject) => { finish = () => failure ? reject(new Error('late error')) : resolve({ requestId, reportId, sha256: retry.sha256, report: report('failed'), retainedExampleId: null, retainedExampleDiagnostic: null }); });
    const pending = controller.select(retry); api.get = get; await controller.select(original); finish(); await pending;
    expect(controller.snapshot().selected?.summary.id).toBe('original'); expect(controller.snapshot().error).toBe('');
  });
  it('ignores inactive requests and loads a fresh history after remount', async () => {
    const { api, controller } = fixture(); let finish!: (v: PreparationHistoryResult) => void; let id = '';
    const list = api.list; api.list = requestId => { id = requestId; return new Promise(resolve => { finish = resolve; }); };
    controller.activate(true); controller.activate(false); finish({ requestId: id, reports: [retry], examples: [] }); await Promise.resolve();
    expect(controller.snapshot().loaded).toBe(false); expect(controller.snapshot().selected).toBeNull();
    api.list = list; await activate(controller); expect(controller.snapshot().selected?.summary.id).toBe('original');
  });
  it.each(['requestId', 'reportId', 'sha256', 'status'])('rejects mismatched detail %s without replacing accepted metadata', async field => {
    const { api, controller } = fixture(); await activate(controller); const selected = controller.snapshot().selected;
    api.get = async (requestId, reportId) => {
      const value: PreparationReportResult = { requestId, reportId, sha256: retry.sha256, report: report('failed'), retainedExampleId: null, retainedExampleDiagnostic: null };
      if (field === 'status') value.report.status = 'passed'; else value[field as 'requestId' | 'reportId' | 'sha256'] = 'wrong';
      return value;
    };
    await controller.select(retry); expect(controller.snapshot().selected).toBe(selected); expect(controller.snapshot().error).toContain('did not match');
  });
  it('treats cancellation as no replacement and exports only the accepted exact-byte identity', async () => {
    const { api, controller } = fixture(); await activate(controller); const selected = controller.snapshot().selected; const exported = vi.spyOn(api, 'export');
    await controller.export(); expect(exported).toHaveBeenCalledWith(expect.any(String), original.id, original.sha256); expect(controller.snapshot().selected).toBe(selected); expect(controller.snapshot().message).toContain('cancelled');
    exported.mockImplementation(async (requestId, reportId, sourceSha256) => ({ requestId, reportId, sourceSha256, file: { name: '報告.json', sha256: original.sha256, sizeBytes: original.sizeBytes } }));
    await controller.export(); expect(controller.snapshot().message).toContain('報告.json'); expect(controller.snapshot().message).toContain(original.sha256); expect(controller.snapshot().selected).toBe(selected);
  });
  it('rejects a rewritten export receipt and retains the report on write failure', async () => {
    const { api, controller } = fixture(); await activate(controller); const selected = controller.snapshot().selected;
    api.export = async (requestId, reportId, sourceSha256) => ({ requestId, reportId, sourceSha256, file: { name: 'report.json', sizeBytes: 99, sha256: original.sha256 } });
    await controller.export(); expect(controller.snapshot().error).toContain('did not match'); expect(controller.snapshot().message).not.toContain('exported');
    api.export = async () => { throw new Error('Destination read-only'); }; await controller.export(); expect(controller.snapshot().error).toBe('Destination read-only'); expect(controller.snapshot().selected).toBe(selected);
  });
  it.each([false, true])('ignores late export responses/failures after navigation and prevents overlapping dialogs (failure=%s)', async failure => {
    const { api, controller } = fixture(); await activate(controller); let finish!: () => void;
    const exported = vi.spyOn(api, 'export').mockImplementation((requestId, reportId, sourceSha256) => new Promise((resolve, reject) => { finish = () => failure ? reject(new Error('old error')) : resolve({ requestId, reportId, sourceSha256, file: null } as PreparationExportResult); }));
    const pending = controller.export(); await controller.export(); expect(exported).toHaveBeenCalledOnce();
    await controller.select(retry); finish(); await pending;
    expect(controller.snapshot().selected?.report.status).toBe('failed'); expect(controller.snapshot().error).toBe(''); expect(controller.snapshot().message).toBe(''); expect(controller.snapshot().exporting).toBe(false);
  });
  it('does not report export completion after becoming inactive', async () => {
    const { api, controller } = fixture(); await activate(controller); let finish!: () => void;
    api.export = (requestId, reportId, sourceSha256) => new Promise(resolve => { finish = () => resolve({ requestId, reportId, sourceSha256, file: { name: 'saved.json', sizeBytes: original.sizeBytes, sha256: original.sha256 } }); });
    const pending = controller.export(); controller.activate(false); finish(); await pending;
    expect(controller.snapshot().message).not.toContain('exported'); expect(controller.snapshot().selected?.summary.id).toBe('original');
  });
});
