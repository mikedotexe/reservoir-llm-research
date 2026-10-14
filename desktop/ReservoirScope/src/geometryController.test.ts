import { describe, expect, it, vi } from 'vitest';
import { GeometryController } from './geometryController';
import { geometryFixture } from './geometryFixtures.test-support';
import type { GeometryApi, GeometryOpenResult } from './geometryTypes';

function setup() {
  const api: GeometryApi = {
    open: vi.fn(async (requestId, syntheticExample) => ({ requestId, cancelled: false, packet: geometryFixture(syntheticExample ? 'syntheticExample' : 'openedFile') })),
    export: vi.fn(async (requestId, packetId) => ({ requestId, packetId, file: null })),
  };
  return { api, controller: new GeometryController(api) };
}
describe('geometry reading lifecycle', () => {
  it('has no automatic import and preserves every accepted reading field on cancel or failure', async () => {
    const { api, controller } = setup();
    expect(controller.snapshot().packet).toBeNull(); expect(api.open).not.toHaveBeenCalled();
    await controller.open(true); controller.select(2); controller.seek(2); controller.coordinate(127); controller.expand(true);
    const accepted = controller.snapshot();
    vi.mocked(api.open).mockImplementationOnce(async requestId => ({ requestId, cancelled: true, packet: null }));
    await controller.open();
    for (const key of ['packet', 'selected', 'frame', 'coordinate', 'coordinatesExpanded'] as const) expect(controller.snapshot()[key]).toEqual(accepted[key]);
    vi.mocked(api.open).mockRejectedValueOnce({ message: 'Changed body bytes' });
    await controller.open();
    expect(controller.snapshot().message).toContain('Changed body bytes');
    for (const key of ['packet', 'selected', 'frame', 'coordinate', 'coordinatesExpanded'] as const) expect(controller.snapshot()[key]).toEqual(accepted[key]);
  });
  it('successful replacement resets reading position and replaces origin even for identical bytes', async () => {
    const { controller } = setup(); await controller.open(true); controller.select(4); controller.expand(true);
    await controller.open(); expect(controller.snapshot().packet?.origin).toBe('openedFile');
    expect(controller.snapshot().selected).toBe(0); expect(controller.snapshot().frame).toBe(0); expect(controller.snapshot().coordinatesExpanded).toBe(false);
    controller.select(2); controller.seek(200); expect(controller.snapshot().frame).toBe(2);
    controller.select(-1); expect(controller.snapshot().selected).toBe(2);
    controller.select(4); expect(controller.snapshot().frame).toBe(0);
  });
  it('serializes open/export and does not accept a mismatched response identity', async () => {
    const { api, controller } = setup(); let finish!: (value: GeometryOpenResult) => void;
    vi.mocked(api.open).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
    const pending = controller.open(true); await controller.open(); await controller.export();
    expect(api.open).toHaveBeenCalledTimes(1); expect(api.export).not.toHaveBeenCalled();
    finish({ requestId: 'wrong-request', cancelled: false, packet: geometryFixture() }); await pending;
    expect(controller.snapshot().packet).toBeNull(); expect(controller.snapshot().busy).toBe(false);
    expect(controller.snapshot().message).toContain('did not match');
  });
  it('keeps synthetic origin on missing example and refuses a mislabeled response', async () => {
    const { api, controller } = setup(); await controller.open(true);
    vi.mocked(api.open).mockRejectedValueOnce(new Error('Example missing from package')); await controller.open(true);
    expect(controller.snapshot().packet?.origin).toBe('syntheticExample');
    vi.mocked(api.open).mockImplementationOnce(async requestId => ({ requestId, cancelled: false, packet: geometryFixture('openedFile') }));
    await controller.open(true); expect(controller.snapshot().packet?.origin).toBe('syntheticExample');
    expect(controller.snapshot().message).toContain('origin did not match');
  });
  it('exports only matching original bytes and preserves the reading on export cancellation', async () => {
    const { api, controller } = setup(); await controller.open(true); controller.select(2); controller.seek(2);
    const packet = controller.snapshot().packet!;
    await controller.export(); expect(controller.snapshot().frame).toBe(2); expect(controller.snapshot().exported).toBeNull();
    vi.mocked(api.export).mockImplementationOnce(async (requestId, packetId) => ({ requestId, packetId, file: { name: 'copy.json', sizeBytes: packet.sizeBytes, sha256: packet.sha256 } }));
    await controller.export(); expect(controller.snapshot().exported?.sha256).toBe(packet.sha256);
    vi.mocked(api.export).mockImplementationOnce(async (requestId, packetId) => ({ requestId, packetId, file: { name: 'wrong.json', sizeBytes: packet.sizeBytes, sha256: 'wrong' } }));
    await controller.export(); expect(controller.snapshot().exported?.name).toBe('copy.json'); expect(controller.snapshot().message).toContain('does not match');
  });
});
