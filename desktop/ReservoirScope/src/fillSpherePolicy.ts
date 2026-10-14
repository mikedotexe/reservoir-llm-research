import { createRenderScheduler, drawingBufferSize } from './renderPolicy';

// The sphere reuses the existing 1M-pixel, DPR<=2, <=4096/hardware policy.
export { drawingBufferSize as fillDrawingBufferSize };
interface Driver { request: (draw: () => void) => number; cancel: (id: number) => void; draw: () => void }
interface Visibility { active: boolean; documentVisible: boolean; inViewport: boolean; contextAvailable: boolean }
/** The active workspace is a separate gate from browser visibility. */
export function createFillScheduler(driver: Driver, initial: Visibility) {
  let current = { ...initial };
  const scheduler = createRenderScheduler(driver, { ...initial, documentVisible: initial.active && initial.documentVisible });
  return {
    invalidate: () => scheduler.invalidate(),
    setVisibility(next: Partial<Visibility>) {
      current = { ...current, ...next };
      scheduler.setVisibility({ ...current, documentVisible: current.active && current.documentVisible });
    },
    dispose: () => scheduler.dispose(),
  };
}
