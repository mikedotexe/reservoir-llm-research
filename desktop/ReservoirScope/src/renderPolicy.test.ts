import { describe, expect, it, vi } from 'vitest';
import { createRenderScheduler, drawingBufferSize, MAX_SURFACE_PIXELS } from './renderPolicy';

describe('bounded surface rasterization', () => {
  it('preserves ordinary native resolution and caps high device density', () => {
    expect(drawingBufferSize(500, 310, 1)).toEqual({ width: 500, height: 310 });
    expect(drawingBufferSize(500, 310, 4)).toEqual({ width: 1000, height: 620 });
  });
  it('bounds total pixels and hardware dimensions across large and narrow windows', () => {
    for (const [width, height, dpr, limit] of [[3840, 2160, 3, 4096], [8000, 100, 2, 4096], [1600, 1200, 2, 512], [0.4, 0.2, 2, 4096]]) {
      const size = drawingBufferSize(width, height, dpr, limit)!;
      expect(size.width * size.height).toBeLessThanOrEqual(MAX_SURFACE_PIXELS);
      expect(Math.max(size.width, size.height)).toBeLessThanOrEqual(limit);
      expect(Math.min(size.width, size.height)).toBeGreaterThanOrEqual(1);
      if (size.height > 1) expect(Math.abs(size.width / width - size.height / height)).toBeLessThanOrEqual(Math.max(1 / width, 1 / height));
    }
  });
  it('does not allocate zero or invalid layout sizes and handles missing DPR', () => {
    for (const invalid of [0, -1, NaN, Infinity]) expect(drawingBufferSize(invalid, 300, 2)).toBeNull();
    expect(drawingBufferSize(400, 300, NaN)).toEqual({ width: 400, height: 300 });
  });
});

function harness(initial = { documentVisible: true, inViewport: true, contextAvailable: true }) {
  let next = 0;
  const queue = new Map<number, () => void>();
  const draw = vi.fn();
  const request = vi.fn((callback: () => void) => { queue.set(++next, callback); return next; });
  const cancel = vi.fn((frame: number) => { queue.delete(frame); });
  const scheduler = createRenderScheduler({ request, cancel, draw }, initial);
  const flush = () => { const batch = [...queue.values()]; queue.clear(); batch.forEach(callback => callback()); };
  return { scheduler, draw, request, cancel, flush, queue };
}

describe('visible, event-driven rendering', () => {
  it('coalesces rapid inputs and schedules no idle follow-up frame', () => {
    const h = harness();
    for (let i = 0; i < 100; i++) h.scheduler.invalidate();
    expect(h.request).toHaveBeenCalledTimes(1);
    h.flush();
    expect(h.draw).toHaveBeenCalledTimes(1);
    expect(h.queue.size).toBe(0);
  });
  it('cancels work leaving the viewport and renders one latest state on return', () => {
    const h = harness();
    h.scheduler.invalidate();
    h.scheduler.setVisibility({ inViewport: false });
    for (let i = 0; i < 20; i++) h.scheduler.invalidate();
    h.flush();
    expect(h.cancel).toHaveBeenCalledTimes(1);
    expect(h.draw).not.toHaveBeenCalled();
    expect(h.queue.size).toBe(0);
    h.scheduler.setVisibility({ inViewport: true });
    h.flush();
    expect(h.draw).toHaveBeenCalledTimes(1);
  });
  it('requires both document visibility and viewport visibility before drawing', () => {
    const h = harness({ documentVisible: false, inViewport: false, contextAvailable: true });
    h.scheduler.invalidate();
    h.scheduler.setVisibility({ inViewport: true });
    h.flush();
    expect(h.request).not.toHaveBeenCalled();
    h.scheduler.setVisibility({ documentVisible: true });
    h.flush();
    expect(h.draw).toHaveBeenCalledTimes(1);
  });
  it('defers changes through context loss and flushes once after recovery', () => {
    const h = harness();
    h.scheduler.invalidate();
    h.scheduler.setVisibility({ contextAvailable: false });
    h.scheduler.invalidate();
    h.flush();
    expect(h.draw).not.toHaveBeenCalled();
    h.scheduler.setVisibility({ contextAvailable: true });
    h.flush();
    expect(h.draw).toHaveBeenCalledTimes(1);
  });
  it('cancels and permanently suppresses work after disposal', () => {
    const h = harness();
    h.scheduler.invalidate();
    h.scheduler.dispose();
    h.scheduler.invalidate();
    h.scheduler.setVisibility({ inViewport: true });
    h.flush();
    expect(h.draw).not.toHaveBeenCalled();
    expect(h.request).toHaveBeenCalledTimes(1);
  });
});
