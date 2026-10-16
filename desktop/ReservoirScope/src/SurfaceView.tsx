import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { createRenderScheduler, drawingBufferSize } from './renderPolicy';
import { buildSurface, clampPose, interpolateField, nearestSite, poseForKey, projectSurface, topographicRadius } from './surfaceMath';
import { DEFAULT_CAMERA, type CameraPose, type ReferenceScene } from './types';

const vertexShader = `
  attribute float field;
  varying float vField;
  varying vec3 vNormal;
  void main() {
    vField = field;
    vNormal = normalize(normalMatrix * normal);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;
const fragmentShader = `
  varying float vField;
  varying vec3 vNormal;
  void main() {
    float t = clamp(vField, -1.0, 1.0);
    vec3 neutral = vec3(0.10, 0.17, 0.23);
    vec3 color = t < 0.0 ? mix(neutral, vec3(0.52, 0.30, 0.92), -t) : mix(neutral, vec3(0.14, 0.91, 0.79), t);
    float lighting = 0.52 + 0.48 * max(0.0, dot(normalize(vNormal), normalize(vec3(-0.5, 0.8, 1.0))));
    color *= lighting;
    float width = max(fwidth(vField) * 1.2, 0.0006);
    float contourDistance = abs(fract(vField / 0.2 + 0.5) - 0.5) * 0.2;
    float contour = 1.0 - smoothstep(width * 0.35, width, contourDistance);
    float zero = 1.0 - smoothstep(width * 0.5, width * 1.4, abs(vField));
    color = mix(color, vec3(0.58, 0.76, 0.82), contour * 0.33);
    color = mix(color, vec3(0.87, 0.97, 0.98), zero * 0.78);
    gl_FragColor = vec4(color, 1.0);
  }
`;

interface Props {
  reference: ReferenceScene;
  selected: number;
  pose: CameraPose;
  onPose: (pose: CameraPose) => void;
  onSelect: (index: number) => void;
  tableOnly: boolean;
  evidenceLabel?: string;
  fixedScale?: number;
  nonnegative?: boolean;
}

export default function SurfaceView({ reference, selected, pose, onPose, onSelect, tableOnly, evidenceLabel = 'Reference scene', fixedScale = 1, nonnegative = false }: Props) {
  const hostRef = useRef<HTMLDivElement>(null);
  const runtimeRef = useRef<{ render: () => void; select: (index: number) => void; camera: (pose: CameraPose) => void; values: (values: number[], selected: number) => void } | null>(null);
  const callbacks = useRef({ onPose, onSelect, pose });
  callbacks.current = { onPose, onSelect, pose };
  const contextExtension = useRef<WEBGL_lose_context | null>(null);
  const [status, setStatus] = useState<'loading' | 'ready' | 'lost' | 'unavailable'>('loading');
  const [detail, setDetail] = useState('Preparing WebGL2…');
  const [renderCount, setRenderCount] = useState(0);
  const [supportsLossTest, setSupportsLossTest] = useState(false);

  useEffect(() => {
    if (tableOnly) { setStatus('unavailable'); setSupportsLossTest(false); setDetail('Table-only mode selected. Exact coordinates remain available below.'); return; }
    const host = hostRef.current;
    if (!host) return;
    // Own a fresh canvas per mount. Cleanup can really release its graphics
    // context without poisoning a future mount (including React StrictMode).
    const canvas = document.createElement('canvas');
    canvas.tabIndex = 0;
    canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-label', `${reference.title}. Signed state topography on a fixed coordinate-index atlas, not network connectivity. Drag or use arrow keys to orbit. Plus and minus zoom. Space resets. Select exact coordinates in the table below.`);
    host.prepend(canvas);
    let renderer: THREE.WebGLRenderer | undefined;
    let geometry: THREE.BufferGeometry | undefined;
    let markerGeometry: THREE.SphereGeometry | undefined;
    let material: THREE.ShaderMaterial | undefined;
    let markerMaterial: THREE.MeshBasicMaterial | undefined;
    let observer: ResizeObserver | undefined;
    let viewportObserver: IntersectionObserver | undefined;
    let scheduler: ReturnType<typeof createRenderScheduler> | undefined;
    let contextLost = false;
    let draws = 0;
    let cleanupEvents = () => {};
    setStatus('loading'); setRenderCount(0); setSupportsLossTest(false);
    try {
      const context = canvas.getContext('webgl2', { antialias: true, alpha: false, powerPreference: 'low-power' });
      if (!context) throw new Error('WebGL2 is unavailable in this webview.');
      renderer = new THREE.WebGLRenderer({ canvas, context, antialias: true });
      renderer.setClearColor(0x071018);
      contextExtension.current = context.getExtension('WEBGL_lose_context');
      setSupportsLossTest(contextExtension.current !== null);
      const world = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(42, 1, 0.05, 20);
      const surface = buildSurface(reference.values, 32, 64, fixedScale);
      let currentValues = reference.values;
      geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(surface.positions, 3));
      geometry.setAttribute('field', new THREE.Float32BufferAttribute(surface.field, 1));
      geometry.setIndex(surface.indices);
      geometry.computeVertexNormals();
      material = new THREE.ShaderMaterial({ vertexShader, fragmentShader });
      const mesh = new THREE.Mesh(geometry, material);
      world.add(mesh);
      markerGeometry = new THREE.SphereGeometry(0.018, 14, 10);
      markerMaterial = new THREE.MeshBasicMaterial({ color: 0xffd79a, depthTest: true });
      const marker = new THREE.Mesh(markerGeometry, markerMaterial);
      world.add(marker);
      const raycaster = new THREE.Raycaster();
      const pointer = new THREE.Vector2();
      const hardwareLimit = context.getParameter(context.MAX_RENDERBUFFER_SIZE) as number;
      let lastWidth = 0, lastHeight = 0;
      let resizeDirty = true;
      const updateDrawingBuffer = () => {
        if (!resizeDirty) return true;
        const { width, height } = host.getBoundingClientRect();
        const size = drawingBufferSize(width, height, window.devicePixelRatio, hardwareLimit);
        if (!size) return false;
        // Pixel ratio stays at 1: these are explicit physical buffer dimensions.
        // Avoid reallocating unchanged buffers during resize/visibility events.
        if (size.width !== lastWidth || size.height !== lastHeight) {
          renderer!.setSize(size.width, size.height, false);
          lastWidth = size.width; lastHeight = size.height;
        }
        camera.aspect = width / height; camera.updateProjectionMatrix();
        resizeDirty = false;
        return true;
      };

      // One coalesced frame per input, camera, size or context change; no idle loop.
      scheduler = createRenderScheduler({
        request: callback => requestAnimationFrame(callback),
        cancel: frame => cancelAnimationFrame(frame),
        draw: () => {
          try {
            if (!updateDrawingBuffer()) return;
            renderer!.render(world, camera);
            draws += 1; setRenderCount(draws);
          } catch (error) {
            setStatus('unavailable'); setDetail(error instanceof Error ? error.message : 'The graphics renderer could not draw this scene.');
          }
        },
      }, { documentVisible: !document.hidden, inViewport: !('IntersectionObserver' in window), contextAvailable: true });
      const requestRender = () => scheduler!.invalidate();
      const updateCamera = (current: CameraPose) => {
        camera.position.set(
          current.distance * Math.cos(current.pitch) * Math.sin(current.yaw),
          current.distance * Math.sin(current.pitch),
          current.distance * Math.cos(current.pitch) * Math.cos(current.yaw),
        );
        camera.lookAt(0, 0, 0); camera.updateMatrixWorld(); requestRender();
      };
      const updateSelection = (index: number) => {
        const direction = new THREE.Vector3(...surface.sites[index]).normalize();
        raycaster.set(direction.clone().multiplyScalar(3), direction.clone().negate());
        const intersection = raycaster.intersectObject(mesh)[0];
        const radius = intersection ? intersection.point.length() : topographicRadius(interpolateField(surface.sites[index], surface.sites, currentValues) / fixedScale);
        marker.position.copy(direction.multiplyScalar(radius + 0.008));
        requestRender();
      };
      const updateValues = (values: number[], index: number) => {
        if (values !== currentValues) {
          const projected = projectSurface(surface, values, fixedScale);
          const position = geometry!.getAttribute('position') as THREE.BufferAttribute;
          const field = geometry!.getAttribute('field') as THREE.BufferAttribute;
          (position.array as Float32Array).set(projected.positions);
          (field.array as Float32Array).set(projected.field);
          position.needsUpdate = true; field.needsUpdate = true;
          geometry!.computeVertexNormals(); geometry!.computeBoundingSphere();
          currentValues = values;
        }
        updateSelection(index);
      };
      const resize = () => {
        resizeDirty = true; requestRender();
      };
      let resolutionQuery: MediaQueryList | undefined;
      const watchResolution = () => {
        resolutionQuery?.removeEventListener('change', watchResolution);
        resolutionQuery = window.matchMedia(`(resolution: ${window.devicePixelRatio || 1}dppx)`);
        resolutionQuery.addEventListener('change', watchResolution);
        resize();
      };
      let drag: { id: number; x: number; y: number; moved: boolean } | null = null;
      const down = (event: PointerEvent) => {
        if (event.button !== 0) return;
        canvas.focus(); canvas.setPointerCapture(event.pointerId);
        drag = { id: event.pointerId, x: event.clientX, y: event.clientY, moved: false };
      };
      const move = (event: PointerEvent) => {
        if (!drag || drag.id !== event.pointerId) return;
        const dx = event.clientX - drag.x, dy = event.clientY - drag.y;
        if (Math.abs(dx) + Math.abs(dy) > 2) drag.moved = true;
        if (!drag.moved) return;
        drag.x = event.clientX; drag.y = event.clientY;
        const current = callbacks.current.pose;
        callbacks.current.onPose(clampPose({ ...current, yaw: current.yaw - dx * 0.007, pitch: current.pitch + dy * 0.007 }));
      };
      const up = (event: PointerEvent) => {
        if (!drag || drag.id !== event.pointerId) return;
        if (!drag.moved && !contextLost) {
          const bounds = canvas.getBoundingClientRect();
          pointer.set((event.clientX - bounds.left) / bounds.width * 2 - 1, -(event.clientY - bounds.top) / bounds.height * 2 + 1);
          raycaster.setFromCamera(pointer, camera);
          const intersection = raycaster.intersectObject(mesh)[0];
          if (intersection) callbacks.current.onSelect(nearestSite(intersection.point.toArray(), surface.sites));
        }
        drag = null;
        if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
      };
      const cancel = () => { drag = null; };
      const wheel = (event: WheelEvent) => {
        event.preventDefault();
        callbacks.current.onPose(clampPose({ ...callbacks.current.pose, distance: callbacks.current.pose.distance + event.deltaY * 0.003 }));
      };
      const key = (event: KeyboardEvent) => {
        if (event.key === ' ' || event.key === 'Home') { event.preventDefault(); callbacks.current.onPose({ ...DEFAULT_CAMERA }); return; }
        const next = poseForKey(callbacks.current.pose, event.key);
        if (next) { event.preventDefault(); callbacks.current.onPose(next); }
      };
      const lost = (event: Event) => {
        event.preventDefault(); contextLost = true;
        canvas.style.visibility = 'hidden';
        scheduler!.setVisibility({ contextAvailable: false });
        setStatus('lost'); setDetail('Graphics context lost. Recorded values are intact; use the exact coordinate table.');
      };
      const restored = () => {
        contextLost = false;
        // Three.js recreates its background state during context restoration.
        // Reapply our explicit clear color before the first recovered frame.
        renderer!.setClearColor(0x071018);
        lastWidth = 0; lastHeight = 0;
        contextExtension.current = context.getExtension('WEBGL_lose_context');
        setSupportsLossTest(contextExtension.current !== null);
        scheduler!.setVisibility({ contextAvailable: true });
        canvas.style.visibility = 'visible'; setStatus('ready'); setDetail('WebGL2 context restored · evidence unchanged'); resize(); requestRender();
      };
      const visible = () => { scheduler!.setVisibility({ documentVisible: !document.hidden }); if (!document.hidden) resize(); };
      canvas.addEventListener('pointerdown', down); canvas.addEventListener('pointermove', move);
      canvas.addEventListener('pointerup', up); canvas.addEventListener('pointercancel', cancel);
      canvas.addEventListener('wheel', wheel, { passive: false }); canvas.addEventListener('keydown', key);
      canvas.addEventListener('webglcontextlost', lost); canvas.addEventListener('webglcontextrestored', restored);
      window.addEventListener('resize', resize); document.addEventListener('visibilitychange', visible);
      cleanupEvents = () => {
        canvas.removeEventListener('pointerdown', down); canvas.removeEventListener('pointermove', move);
        canvas.removeEventListener('pointerup', up); canvas.removeEventListener('pointercancel', cancel);
        canvas.removeEventListener('wheel', wheel); canvas.removeEventListener('keydown', key);
        canvas.removeEventListener('webglcontextlost', lost); canvas.removeEventListener('webglcontextrestored', restored);
        window.removeEventListener('resize', resize); document.removeEventListener('visibilitychange', visible);
        resolutionQuery?.removeEventListener('change', watchResolution);
      };
      observer = new ResizeObserver(resize); observer.observe(host);
      if ('IntersectionObserver' in window) {
        viewportObserver = new IntersectionObserver(entries => {
          const entry = entries.find(item => item.target === host);
          // At threshold 0 an edge touch may be the only entering callback.
          // Allow that draw so a later positive intersection cannot stay culled.
          if (entry) scheduler!.setVisibility({ inViewport: entry.isIntersecting });
        });
        viewportObserver.observe(host);
      }
      runtimeRef.current = { render: requestRender, select: updateSelection, camera: updateCamera, values: updateValues };
      updateCamera(callbacks.current.pose); updateSelection(selected); watchResolution();
      setStatus('ready'); setDetail('WebGL2 · draws only when something changes');
    } catch (error) {
      canvas.style.visibility = 'hidden';
      setStatus('unavailable'); setDetail(error instanceof Error ? error.message : 'The graphics renderer is unavailable.');
    }
    return () => {
      scheduler?.dispose(); cleanupEvents(); observer?.disconnect(); viewportObserver?.disconnect();
      runtimeRef.current = null; contextExtension.current = null;
      geometry?.dispose(); markerGeometry?.dispose(); material?.dispose(); markerMaterial?.dispose(); renderer?.dispose();
      renderer?.forceContextLoss(); canvas.remove();
    };
  }, [reference.id, reference.nodeCount, tableOnly, fixedScale]);

  useEffect(() => { runtimeRef.current?.camera(pose); }, [pose]);
  useEffect(() => { runtimeRef.current?.values(reference.values, selected); }, [reference.values, selected]);
  useEffect(() => {
    hostRef.current?.querySelector('canvas')?.setAttribute('aria-label', `${reference.title}. ${nonnegative ? 'Nonnegative magnitude' : 'Signed field'} topography on a fixed coordinate-index atlas, not network connectivity. Drag or use arrow keys to orbit. Plus and minus zoom. Space resets. Select exact coordinates in the table below.`);
  }, [reference.title, nonnegative, tableOnly, fixedScale]);

  return <section className="scene-card" aria-label={reference.title}>
    <div className="scene-heading"><div><span className="eyebrow">{reference.nodeCount} COORDINATES</span><h3>{reference.title}</h3></div><span className="subtle-tag">{evidenceLabel}</span></div>
    <div className="scene-canvas" ref={hostRef}>
      {status !== 'ready' && <div className="graphics-fallback" role="status"><span className="fallback-icon">◇</span><strong>{status === 'loading' ? 'Preparing the surface' : 'Exact values remain available'}</strong><p>{detail}</p></div>}
      {status === 'ready' && <div className="scene-corner">{nonnegative ? 'ACTIVATION MAGNITUDE' : 'SIGNED COORDINATES'}<br /><span>Fixed scale {nonnegative ? '0' : `−${fixedScale}`} to +{fixedScale}</span></div>}
    </div>
    <div className="scene-controls"><span className={status === 'ready' ? 'status-ready' : 'status-warning'}>{status === 'ready' ? '●' : '○'} {status === 'ready' ? '3D ready' : status === 'lost' ? 'Context lost' : status === 'loading' ? 'Loading' : 'Table fallback'}</span><button className="text-button" onClick={() => onPose({ ...DEFAULT_CAMERA })}>Reset camera</button></div>
    {nonnegative ? <div className="legend legend-nonnegative"><span>0</span><div style={{ background: 'linear-gradient(to right,#192b3b,#24bf9f)' }}/><span>+{fixedScale}</span></div> : <div className="legend"><span>−{fixedScale}</span><div /><span>0</span><div /><span>+{fixedScale}</span></div>}
    <p className="scene-note">Drag to orbit · click to inspect · arrow keys to orbit · +/− to zoom. Contours every {Number((fixedScale / 5).toPrecision(6))}; the bright line marks zero. Display relief and color saturate at the fixed scale; exact values remain unchanged.</p>
    <details className="qualification-tools"><summary>Graphics diagnostics</summary><p>WebGL2 · {renderCount} frames drawn</p><p>This explicit test temporarily removes the graphics context. Values and selection stay available.</p><div className="button-row"><button disabled={!supportsLossTest || status !== 'ready'} onClick={() => contextExtension.current?.loseContext()}>Lose graphics context</button><button disabled={status !== 'lost'} onClick={() => contextExtension.current?.restoreContext()}>Restore context</button></div>{!supportsLossTest && <p>This webview does not expose the context-loss testing extension.</p>}</details>
  </section>;
}
