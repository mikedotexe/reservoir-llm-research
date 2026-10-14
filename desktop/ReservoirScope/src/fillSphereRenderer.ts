import * as THREE from 'three';
import { fillGeometryKey, fillRadius, referenceRings, type FillReferences } from './fillSphereMath';
import { createFillScheduler, fillDrawingBufferSize } from './fillSpherePolicy';

export interface FillGraphicsStatus {
  state: 'ready' | 'lost' | 'unavailable'; detail: string; frames: number; supportsRecovery: boolean;
}
export interface FillSphereRenderer {
  update: (fillPercent: number, references?: FillReferences | null) => void;
  loseContext: () => void;
  restoreContext: () => void;
  dispose: () => void;
}
const BACKGROUND = 0x08151e;
const VERTEX = `varying vec3 vNormal; varying vec3 vPosition;
void main(){vNormal=normalize(normalMatrix*normal);vPosition=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`;
const FRAGMENT = `varying vec3 vNormal; varying vec3 vPosition;
void main(){
  if(vPosition.z>0.0) discard;
  float light=0.48+0.52*max(0.0,dot(normalize(vNormal),normalize(vec3(-0.5,0.8,1.0))));
  float edge=pow(1.0-abs(normalize(vNormal).z),2.0);
  vec3 color=mix(vec3(0.035,0.32,0.39),vec3(0.26,0.90,0.80),edge)*light;
  gl_FragColor=vec4(color,0.86);
}`;
function circleGeometry(segments = 192) {
  const positions = new Float32Array((segments + 1) * 3);
  for (let i = 0; i <= segments; i++) { const a = i / segments * Math.PI * 2; positions[i*3] = Math.cos(a); positions[i*3+1] = Math.sin(a); }
  return new THREE.BufferGeometry().setAttribute('position', new THREE.BufferAttribute(positions, 3));
}

/** One owned canvas/context, fixed geometry and no autonomous animation loop. */
export function mountFillSphere(host: HTMLDivElement, notify: (status: FillGraphicsStatus) => void): FillSphereRenderer {
  const canvas = document.createElement('canvas');
  canvas.setAttribute('aria-hidden', 'true'); // Exact values and meaning are in the adjacent DOM.
  host.prepend(canvas);
  let renderer: THREE.WebGLRenderer | undefined;
  let contextHandle: WebGL2RenderingContext | null = null;
  const geometries: THREE.BufferGeometry[] = [];
  const materials: THREE.Material[] = [];
  let scheduler: ReturnType<typeof createFillScheduler> | undefined;
  let resizeObserver: ResizeObserver | undefined;
  let viewportObserver: IntersectionObserver | undefined;
  let resolutionQuery: MediaQueryList | undefined;
  let extension: WEBGL_lose_context | null = null;
  let disposed = false, lost = false, frames = 0;
  let removeEvents = () => {};
  const dispose = () => {
    if (disposed) return; disposed = true;
    scheduler?.dispose(); removeEvents(); resizeObserver?.disconnect(); viewportObserver?.disconnect();
    for (const geometry of geometries) geometry.dispose();
    for (const material of materials) material.dispose();
    renderer?.dispose();
    if (contextHandle && !contextHandle.isContextLost()) extension?.loseContext();
    extension = null; contextHandle = null; canvas.remove();
  };
  try {
    const context = canvas.getContext('webgl2', { antialias: true, alpha: false, powerPreference: 'low-power' });
    if (!context) throw new Error('WebGL2 is unavailable. Exact retained values remain available.');
    contextHandle = context; extension = context.getExtension('WEBGL_lose_context');
    renderer = new THREE.WebGLRenderer({ canvas, context, antialias: true });
    renderer.setClearColor(BACKGROUND);
    const world = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1.2, 1.2, 1.2, -1.2, 0.1, 10);
    camera.position.set(0.38, 0.18, 4); camera.lookAt(0, 0, 0);
    const sphereGeometry = new THREE.SphereGeometry(1, 64, 32); geometries.push(sphereGeometry);
    const filledMaterial = new THREE.ShaderMaterial({ vertexShader: VERTEX, fragmentShader: FRAGMENT, transparent: true, side: THREE.DoubleSide }); materials.push(filledMaterial);
    const fill = new THREE.Mesh(sphereGeometry, filledMaterial); world.add(fill);
    const faceGeometry = new THREE.CircleGeometry(1, 96); geometries.push(faceGeometry);
    const faceMaterial = new THREE.MeshBasicMaterial({ color: 0x50dccb, opacity: 0.12, transparent: true, depthWrite: false, side: THREE.DoubleSide }); materials.push(faceMaterial);
    const face = new THREE.Mesh(faceGeometry, faceMaterial); face.position.z = 0.003; world.add(face);
    const circle = circleGeometry(); geometries.push(circle);
    const createLine = (color: number, opacity: number, dashed = false) => {
      const material = dashed
        ? new THREE.LineDashedMaterial({ color, opacity, transparent: true, dashSize: 0.034, gapSize: 0.023, depthWrite: false })
        : new THREE.LineBasicMaterial({ color, opacity, transparent: true, depthWrite: false });
      materials.push(material);
      const line = new THREE.Line(circle, material); if (!circle.getAttribute('lineDistance')) line.computeLineDistances(); world.add(line); return line;
    };
    const cage = createLine(0xc9e6ea, 0.55); cage.position.z = 0.012;
    for (const [x,y] of [[Math.PI/2,0],[0,Math.PI/2],[Math.PI/4,Math.PI/4]]) {
      const line = createLine(0x8aadbc, 0.18); line.rotation.set(x,y,0);
    }
    const boundary = createLine(0x8affdf, 0.95); boundary.position.z = 0.014;
    const rings = Array.from({ length: 5 }, (_, index) => {
      const line = createLine(0xffffff, index === 1 ? 0.87 : 0.55, index === 1 || index >= 3); line.position.z = 0.011; line.visible = false; return line;
    });
    let key = '', width = 0, height = 0, resizeDirty = true;
    const hardwareLimit = context.getParameter(context.MAX_RENDERBUFFER_SIZE) as number;
    const resize = () => { resizeDirty = true; scheduler?.invalidate(); };
    const draw = () => {
      if (disposed || lost) return;
      try {
        if (resizeDirty) {
          const bounds = host.getBoundingClientRect();
          const size = fillDrawingBufferSize(bounds.width, bounds.height, window.devicePixelRatio, hardwareLimit);
          if (!size) return;
          if (size.width !== width || size.height !== height) { renderer!.setSize(size.width,size.height,false); width = size.width; height = size.height; }
          const aspect = bounds.width / bounds.height;
          const halfHeight = Math.max(1.16, 1.16 / aspect);
          camera.left = -halfHeight * aspect; camera.right = halfHeight * aspect; camera.top = halfHeight; camera.bottom = -halfHeight;
          camera.updateProjectionMatrix(); resizeDirty = false;
        }
        renderer!.render(world,camera); frames++;
        notify({ state: 'ready', detail: 'WebGL2 · recorded value shown directly', frames, supportsRecovery: extension !== null });
      } catch (error) {
        scheduler?.setVisibility({ contextAvailable: false }); canvas.style.visibility = 'hidden';
        notify({ state: 'unavailable', detail: error instanceof Error ? error.message : 'Graphics unavailable; exact values retained.', frames, supportsRecovery: false });
      }
    };
    scheduler = createFillScheduler({ request: callback => requestAnimationFrame(callback), cancel: id => cancelAnimationFrame(id), draw },
      { active: true, documentVisible: !document.hidden, inViewport: !('IntersectionObserver' in window), contextAvailable: true });
    const lostEvent = (event: Event) => {
      event.preventDefault(); lost = true; canvas.style.visibility = 'hidden'; scheduler!.setVisibility({ contextAvailable: false });
      notify({ state: 'lost', detail: 'Graphics context lost. The retained value and references are unchanged.', frames, supportsRecovery: extension !== null });
    };
    const restoreEvent = () => {
      if (disposed) return;
      lost = false; renderer!.setClearColor(BACKGROUND); extension = context.getExtension('WEBGL_lose_context');
      width = 0; height = 0; resizeDirty = true; canvas.style.visibility = 'visible';
      scheduler!.setVisibility({ contextAvailable: true }); scheduler!.invalidate();
    };
    const visible = () => { scheduler!.setVisibility({ documentVisible: !document.hidden }); if (!document.hidden) resize(); };
    const resolution = () => {
      resolutionQuery?.removeEventListener('change', resolution);
      resolutionQuery = window.matchMedia(`(resolution: ${window.devicePixelRatio || 1}dppx)`);
      resolutionQuery.addEventListener('change', resolution); resize();
    };
    canvas.addEventListener('webglcontextlost', lostEvent); canvas.addEventListener('webglcontextrestored', restoreEvent);
    document.addEventListener('visibilitychange',visible); window.addEventListener('resize',resize);
    removeEvents = () => {
      canvas.removeEventListener('webglcontextlost',lostEvent); canvas.removeEventListener('webglcontextrestored',restoreEvent);
      document.removeEventListener('visibilitychange',visible); window.removeEventListener('resize',resize);
      resolutionQuery?.removeEventListener('change',resolution);
    };
    resizeObserver = new ResizeObserver(resize); resizeObserver.observe(host);
    if ('IntersectionObserver' in window) {
      viewportObserver = new IntersectionObserver(entries => {
        const entry = entries.find(row => row.target === host);
        // Edge contact at threshold zero must not leave the scene permanently culled.
        if (entry) scheduler!.setVisibility({ inViewport: entry.isIntersecting });
      }); viewportObserver.observe(host);
    }
    resolution();
    return {
      update(fillPercent,references) {
        const radius = fillRadius(fillPercent);
        if (disposed || radius === null) return;
        const next = fillGeometryKey(fillPercent,references); if (next === key) return; key = next;
        fill.scale.setScalar(radius); face.scale.setScalar(radius); boundary.scale.setScalar(radius);
        fill.visible = face.visible = boundary.visible = radius > 0;
        const reference = referenceRings(references);
        rings.forEach((line,index) => {
          const row = reference[index]; line.visible = !!row;
          if (row) { line.scale.setScalar(row.radius); line.material.color.setHex(row.color); }
        });
        scheduler!.invalidate();
      },
      loseContext() { if (!disposed && !lost) extension?.loseContext(); },
      restoreContext() { if (!disposed && lost) extension?.restoreContext(); },
      dispose,
    };
  } catch (error) { dispose(); throw error; }
}
