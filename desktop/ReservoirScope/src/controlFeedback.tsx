import type { SustainedControlDiagnostics } from './myReservoirTypes';

const record = (v: unknown): v is Record<string, unknown> => v !== null && typeof v === 'object' && !Array.isArray(v);
const bytes = (v: string) => new TextEncoder().encode(v).length;
const count = (v: unknown): v is number => typeof v === 'number' && Number.isSafeInteger(v) && v >= 0 && v <= 1_048_576;
export function validControlDiagnostics(v: unknown): v is SustainedControlDiagnostics {
  return record(v) && ['next', 'reservoirInput', 'inquiry'].every(key => {
    const d = v[key];
    if (!record(d) || !count(d.candidateCount) || typeof d.explanation !== 'string' || !d.explanation || bytes(d.explanation) > 1024) return false;
    if (d.candidateCount === 0) return d.candidate === null;
    const c = d.candidate;
    return record(c) && count(c.line) && c.line > 0 && typeof c.excerpt === 'string' && !!c.excerpt && bytes(c.excerpt) <= 256
      && typeof c.truncated === 'boolean' && (!c.truncated || bytes(c.excerpt) > 252);
  });
}
export function sameControlDiagnostics(a?: SustainedControlDiagnostics, b?: SustainedControlDiagnostics): boolean {
  if (!a || !b) return a === b;
  return (['next', 'reservoirInput', 'inquiry'] as const).every(key => {
    const x = a[key], y = b[key];
    return x.explanation === y.explanation && x.candidateCount === y.candidateCount
      && x.candidate?.line === y.candidate?.line && x.candidate?.excerpt === y.candidate?.excerpt && x.candidate?.truncated === y.candidate?.truncated;
  });
}
export function ControlFeedback({ diagnostics }: { diagnostics?: SustainedControlDiagnostics }) {
  if (!diagnostics) return null;
  return <details className="my-reservoir-details"><summary>Control feedback</summary>
    <p>These explanations will accompany the result in the next ordinary prompt. Quoted candidates are previous writing, not accepted commands.</p>
    {(['next', 'reservoirInput', 'inquiry'] as const).map(key => {
      const d = diagnostics[key];
      return <div key={key}><h5>{{ next: 'NEXT', reservoirInput: 'Text input', inquiry: 'Inquiry' }[key]}</h5><p>{d.explanation}</p>
        {d.candidate && <><p>{d.candidateCount} control-looking line(s); last at line {d.candidate.line}{d.candidate.truncated ? ' · excerpt truncated' : ''}</p><pre className="my-reservoir-probe-vector">{d.candidate.excerpt}</pre></>}
      </div>;
    })}
  </details>;
}
