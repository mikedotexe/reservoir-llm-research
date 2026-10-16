import { useEffect, useState } from 'react';
import { api, errorText } from './api';
import SurfaceView from './SurfaceView';
import CoordinateInspector from './CoordinateInspector';
import { validateScene } from './surfaceMath';
import { DEFAULT_CAMERA, type BuildInfo, type CameraPose, type FileProof, type ReferenceScene } from './types';

export default function DesktopDiagnostics() {
  const [info, setInfo] = useState<BuildInfo | null>(null);
  const [scenes, setScenes] = useState<ReferenceScene[]>([]);
  const [buildError, setBuildError] = useState('');
  const [sceneError, setSceneError] = useState('');
  const [loading, setLoading] = useState(true);
  const [pose, setPose] = useState<CameraPose>({ ...DEFAULT_CAMERA });
  const [selection, setSelection] = useState<Record<string, number>>({});
  const [tableOnly, setTableOnly] = useState(false);
  const [fileProof, setFileProof] = useState<FileProof | null>(null);
  const [proofMessage, setProofMessage] = useState('');
  const [proofBusy, setProofBusy] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.allSettled([api.buildInfo(), api.scenes()]).then(([build, references]) => {
      if (!active) return;
      if (build.status === 'fulfilled') setInfo(build.value); else setBuildError(errorText(build.reason));
      if (references.status === 'fulfilled') {
        try {
          if (references.value.scenes.length !== 2 || new Set(references.value.scenes.map(scene => scene.nodeCount)).size !== 2) throw new Error('Expected one 32-coordinate and one 128-coordinate reference scene.');
          references.value.scenes.forEach(validateScene);
          setScenes(references.value.scenes);
        } catch (error) { setSceneError(errorText(error)); }
      } else setSceneError(errorText(references.reason));
      setLoading(false);
    });
    return () => { active = false; };
  }, []);

  async function fileAction(kind: 'open' | 'save') {
    setProofBusy(true); setProofMessage('');
    try {
      const proof = await (kind === 'open' ? api.openProof() : api.saveProof());
      if (proof) { setFileProof(proof); setProofMessage(kind === 'open' ? 'Selected file read and hashed. This is a file-access check, not experiment verification.' : 'Original reference-scene bytes exported to the chosen destination.'); }
      else setProofMessage('Dialog cancelled. Previous result retained.');
    } catch (error) { setProofMessage(errorText(error)); }
    finally { setProofBusy(false); }
  }

  return <>
        <section className="qualification-section" aria-labelledby="reference-heading">
          <div className="section-heading"><div><span className="eyebrow">RESERVOIR SURFACES</span><h2 id="reference-heading">Reference scenes</h2><p>Fixed signed scale · linked camera · original values below.</p></div><label className="checkbox-label"><input type="checkbox" checked={tableOnly} onChange={event => setTableOnly(event.target.checked)} /> Exact values without 3D</label></div>
          <div className="fill-availability"><span className="eyebrow">FILL</span><p><strong>Not included in these references.</strong> Fill is a separate measure; surface height represents signed state.</p></div>
          {loading && <div className="notice" role="status">Loading desktop identity and reference resources…</div>}
          {sceneError && <div className="notice warning" role="alert"><strong>Reference scenes unavailable</strong><p>{sceneError}</p><span>No substitute values are shown.</span></div>}
          <div className="scene-grid">{scenes.map(reference => <div className="reference-column" key={reference.id}>
            <SurfaceView reference={reference} selected={selection[reference.id] ?? 0} pose={pose} onPose={setPose} onSelect={index => setSelection(previous => ({ ...previous, [reference.id]: index }))} tableOnly={tableOnly} />
            <CoordinateInspector reference={reference} selected={selection[reference.id] ?? 0} onSelect={index => setSelection(previous => ({ ...previous, [reference.id]: index }))} />
          </div>)}</div>
          {scenes.length > 0 && <p className="mapping-note">Surface height is a fixed display mapping: 0.82 + 0.16 × signed field. It is independent of fill. The fixed index atlas does not represent anatomy or network connections. Renderer conformance and platform acceptance are still being qualified.</p>}
        </section>
        <section className="foundation-grid">
          <div className="info-card"><span className="eyebrow">FILE ACCESS</span><h2>File dialog checks</h2><p>Exercise the native Open and Save dialogs. Opening reads a bounded file and reports its hash. It does not import into a Library.</p><div className="button-row"><button className="primary-button" disabled={proofBusy || !info} onClick={() => fileAction('open')}>Open a file… <span aria-hidden="true">↗</span></button><button disabled={proofBusy || !info} onClick={() => fileAction('save')}>Export reference scenes…</button></div><p className="operation-message" role="status">{proofBusy ? 'Waiting for the native dialog…' : proofMessage}</p>{fileProof && <dl className="proof-details"><dt>File</dt><dd>{fileProof.name}</dd><dt>Size</dt><dd>{fileProof.sizeBytes.toLocaleString()} bytes</dd><dt>SHA-256</dt><dd className="hash">{fileProof.sha256}</dd></dl>}</div>
          <div className="info-card"><span className="eyebrow">BUILD & RESOURCES</span><h2>App version and resources</h2>{info ? <><dl><dt>Desktop</dt><dd>{info.appName} {info.version}</dd><dt>Platform</dt><dd>{info.platform} / {info.arch}</dd><dt>Resources</dt><dd>{info.resourceStatus}</dd></dl><details><summary>Identity and resource hashes</summary><p className="hash">{info.sourceIdentity}</p>{info.resources.map(resource => <div className="resource-row" key={resource.name}><strong>{resource.name}</strong><span>{resource.status}</span><code>{resource.sha256}</code></div>)}{info.appDataDir && <><p>Separate desktop application data</p><code className="hash">{info.appDataDir}</code></>}</details></> : <p className="status-warning" role="status">{buildError || 'Waiting for desktop identity…'}</p>}<p className="fine-print">Packaging and automated checks do not establish human acceptance or parity on another operating system.</p></div>
        </section>
  </>;
}
