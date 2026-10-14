import type { ReferenceScene } from './types';

export default function CoordinateInspector({ reference, selected, onSelect, fixedScale = 1, sourceNote = 'The source path is a provenance label. This view reads the packaged reference, never that historical path.' }: { reference: ReferenceScene; selected: number; onSelect: (index: number) => void; fixedScale?: number; sourceNote?: string }) {
  return <section className="coordinate-inspector" aria-label={`${reference.title} exact coordinates`}>
    <div className="selected-coordinate"><div><span className="eyebrow">SELECTED COORDINATE</span><label>Node <select value={selected} aria-label={`${reference.title} selected coordinate`} onChange={event => onSelect(Number(event.target.value))}>{reference.values.map((_, index) => <option key={index} value={index}>{index}</option>)}</select></label></div><output aria-live="polite">{reference.values[selected].toString()}</output></div>
    <div className="coordinate-matrix" aria-label="Coordinate selection grid">{reference.values.map((value, index) => <button key={index} aria-label={`Inspect coordinate ${index}: ${value}`} aria-pressed={selected === index} tabIndex={selected === index ? 0 : -1} onKeyDown={event => {
      const matrix = event.currentTarget.parentElement!;
      const columns = getComputedStyle(matrix).gridTemplateColumns.split(' ').length;
      const delta = event.key === 'ArrowLeft' ? -1 : event.key === 'ArrowRight' ? 1 : event.key === 'ArrowUp' ? -columns : event.key === 'ArrowDown' ? columns : null;
      if (delta === null && event.key !== 'Home' && event.key !== 'End') return;
      event.preventDefault();
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? reference.values.length - 1 : Math.max(0, Math.min(reference.values.length - 1, index + delta!));
      onSelect(next);
      (matrix.children[next] as HTMLButtonElement).focus();
    }} className={selected === index ? 'selected' : ''} style={{ backgroundColor: value < 0 ? `rgba(150, 97, 239, ${0.13 + Math.min(1, Math.abs(value) / fixedScale) * 0.75})` : `rgba(68, 222, 191, ${0.13 + Math.min(1, Math.abs(value) / fixedScale) * 0.75})` }} onClick={() => onSelect(index)}>{index}</button>)}</div>
    <details><summary>Exact coordinate table · {reference.nodeCount} values</summary><div className="table-scroll"><table><caption>{reference.title} · original signed values</caption><thead><tr><th scope="col">Coordinate</th><th scope="col">Value</th></tr></thead><tbody>{reference.values.map((value, index) => <tr key={index} className={selected === index ? 'selected-row' : ''}><th scope="row"><button aria-label={`Select ${reference.title} coordinate ${index}`} onClick={() => onSelect(index)}>{index}</button></th><td>{value.toString()}</td></tr>)}</tbody></table></div></details>
    <details className="source-details"><summary>Source and measurement limits</summary><p>{reference.description}</p><p>{reference.provenance}</p>{reference.step !== undefined && <p>Recorded step: {reference.step}</p>}{reference.sourcePath && <code className="hash">{reference.sourcePath}</code>}{reference.sourceSha256 && <p className="hash">SHA-256 · {reference.sourceSha256}</p>}<p>{sourceNote}</p></details>
  </section>;
}
