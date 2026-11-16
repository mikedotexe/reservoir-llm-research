import type { ExperimentReport } from './experiments';
import type { SustainedActionReceipt } from './myReservoirTypes';
const n=(v:number)=>v===0?'0':Number(v.toPrecision(4)).toString();
const outcome={measured:'Copied measurements completed',noContrast:'No distinguishing contrast',noExcitation:'Zero additional probe stimulus',unresolved:'Response unresolved'};
export function ExperimentReceiptView({receipt:r}:{receipt:SustainedActionReceipt}) {
 return <>{r.experiment&&<><p><strong>{r.experiment.outcome?outcome[r.experiment.outcome]:'Experiment rejected'}</strong>. {r.experiment.explanation}</p>{r.experiment.reportId&&<p className="sonar-id">Result {r.experiment.reportId}</p>}</>}
 {r.experimentProbe&&<><p>{r.experimentProbe.rejection?'No experiment impulse applied.':`Real impulse: observed immediate recurrent effect ${n(r.stateDeltaL2)}, fresh copied forecast ${n(r.experimentProbe.forecastResponseL2[0])}. Bound 0.05.`}</p><p>The source experiment supplies a direction and measured amplitude. Its copied control settings do not change the live settings. Later forecast values are predictions; only the immediate paired effect is observed.</p><details><summary>Exact experiment impulse receipt</summary><pre>{JSON.stringify(r.experimentProbe,null,2)}</pre></details></>}
 </>;
}
export function ExperimentView({report:r}:{report:ExperimentReport}) {
 return <section className="sonar-report"><h4>{r.request.name} · {outcome[r.outcome]}</h4>
 {r.request.question&&<p>{r.request.question}</p>}<p><strong>{r.explanation}</strong></p>
 <p>Copied origin step {r.origin.step} · requested at {r.requestedStep} · {r.request.probe.waveform.kind} · {r.numericalSteps} copied numerical steps. A turn-start origin precedes that entry’s text-input choice.</p>
 <p>Each condition uses its own unperturbed comparison with matched forcing and noise. These recurrent measurements do not simulate future writing or sensory evolution.</p>
 <div className="experiment-table"><table><thead><tr><th>Condition</th><th>Peak input L2 / sign</th>{r.request.observe.steps.map(t=><th key={t}>Step {t}</th>)}<th>Peak response</th><th>Return step</th></tr></thead><tbody>{r.responses.map((v,i)=><tr key={i}><td>{r.request.conditions[v.condition].label}</td><td>{n(v.amplitude)} / {v.sign}</td>{v.responseL2.map((x,j)=><td key={j}>{n(x)}</td>)}<td>{n(v.peakL2)}</td><td>{v.returnStep??'unresolved'}</td></tr>)}</tbody></table></div>
 <p>Values are recurrent L2 distances from each condition’s no-probe baseline. Return requires five consecutive boundaries below 10% of peak after the last stimulus.</p>
 {r.contrasts.length>0&&<><h5>Between-condition response contrast</h5><div className="experiment-table"><table><thead><tr><th>Input L2 / sign</th>{r.request.observe.steps.map(t=><th key={t}>Step {t}</th>)}</tr></thead><tbody>{r.contrasts.map((v,i)=><tr key={i}><td>{n(v.amplitude)} / {v.sign}</td>{v.responseGapL2.map((x,j)=><td key={j}>{n(x)}</td>)}</tr>)}</tbody></table></div></>}
 <p className="sonar-id">Result {r.id}{r.request.followUpOf&&` · follow-up request ${r.request.followUpOf}`}</p>
 <details><summary>Conditions, coordinates, asymmetry, amplitude scaling and provenance</summary><pre>{JSON.stringify(r,null,2)}</pre></details>
 </section>;
}
