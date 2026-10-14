// Bound raster work independently of window size; numerical geometry is unchanged.
export const MAX_SURFACE_PIXELS = 1_000_000;
export const MAX_SURFACE_DPR = 2;
export const MAX_SURFACE_DIMENSION = 4096;

export function drawingBufferSize(width: number, height: number, dpr: number, hardwareLimit = MAX_SURFACE_DIMENSION) {
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) return null;
  const density = Number.isFinite(dpr) && dpr > 0 ? dpr : 1;
  const dimension = Number.isFinite(hardwareLimit) && hardwareLimit >= 1
    ? Math.min(MAX_SURFACE_DIMENSION, Math.floor(hardwareLimit)) : MAX_SURFACE_DIMENSION;
  const scale = Math.min(density, MAX_SURFACE_DPR, Math.sqrt(MAX_SURFACE_PIXELS / (width * height)), dimension / width, dimension / height);
  return { width: Math.max(1, Math.floor(width * scale)), height: Math.max(1, Math.floor(height * scale)) };
}

interface RenderVisibility { documentVisible: boolean; inViewport: boolean; contextAvailable: boolean }
interface FrameDriver { request: (callback: () => void) => number; cancel: (frame: number) => void; draw: () => void }

/** Retain only the latest invalidation while suspended; never run an idle loop. */
export function createRenderScheduler(driver: FrameDriver, initial: RenderVisibility) {
  let visibility = { ...initial };
  let pending: number | null = null;
  let dirty = false;
  let disposed = false;
  const canDraw = () => !disposed && visibility.documentVisible && visibility.inViewport && visibility.contextAvailable;
  const schedule = () => {
    if (!dirty || !canDraw() || pending !== null) return;
    pending = driver.request(() => {
      pending = null;
      if (!dirty || !canDraw()) return;
      dirty = false;
      driver.draw();
    });
  };
  const cancel = () => { if (pending !== null) driver.cancel(pending); pending = null; };
  return {
    invalidate() { if (!disposed) { dirty = true; schedule(); } },
    setVisibility(next: Partial<RenderVisibility>) {
      visibility = { ...visibility, ...next };
      if (!canDraw()) cancel(); else schedule();
    },
    dispose() { disposed = true; dirty = false; cancel(); },
  };
}
