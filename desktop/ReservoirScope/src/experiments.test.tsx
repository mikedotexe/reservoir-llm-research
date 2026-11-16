import {describe,it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import view from './fixtures/experiments/experiment-view.json';
import actions from './fixtures/experiments/experiment-actions.json';
import {validExperimentRequest, validExperimentReport, type ExperimentReport} from './experiments';
import {validSonarView} from './sonar';
import {validActionReceipt, validAuthoredActionConfig, withAuthoredActionMode} from './authoredActions';
import {DEFAULT_SUSTAINED_CONFIG, type SustainedActionReceipt} from './myReservoirTypes';
import {ExperimentView,ExperimentReceiptView} from './MyReservoirExperiments';
import {SonarSetup} from './MyReservoirSonar';
const config={...withAuthoredActionMode(DEFAULT_SUSTAINED_CONFIG,'authored-v3'),controlFeedback:'diagnostic-v1' as const,sonar:{version:'experiments-v3' as const,allowLiveProbe:true}};
describe('native parameterized experiment contract',()=>{
 it('admits real native reports and receipts with opt-in capability',()=>{
  expect(validAuthoredActionConfig(config)).toBe(true);
  expect(validSonarView(view,view.sessionId,view.generation)).toBe(true);
  for(const r of view.modelExperiments){expect(validExperimentRequest(r.request)).toBe(true);expect(validExperimentReport(r)).toBe(true);}
  for(const raw of actions.state.recentReceipts){const r=raw as SustainedActionReceipt;expect(validActionReceipt(r,view.step,config)).toBe(true);if(r.request?.kind==='experiment'||r.request?.kind==='probeExperiment')expect(validActionReceipt(r,view.step,{...config,sonar:{...config.sonar,version:'compact-scan-v2'}})).toBe(false);}
 });
 it('refuses malformed waveform, unmatched dimensions and invented probe effects',()=>{
  const r=structuredClone(view.modelExperiments[0]);expect(validExperimentReport({...r,responses:r.responses.slice(1)})).toBe(false);
  expect(validExperimentRequest({...r.request,probe:{...r.request.probe,waveform:{kind:'pulseTrain',spacing:64,count:16}}})).toBe(false);
  expect(validExperimentRequest({...r.request,observe:{steps:[1,2],coordinates:[31,32]}})).toBe(false);
  const probe=actions.state.recentReceipts.find(r=>r.request?.kind==='probeExperiment') as SustainedActionReceipt;
  expect(probe).toBeDefined();expect(validActionReceipt({...probe,stateDeltaL2:0},view.step,config)).toBe(false);
  expect(validActionReceipt(probe,view.step,{...config,sonar:{...config.sonar,allowLiveProbe:false}})).toBe(false);
 });
 it('renders copied conditions, outcomes, reference identity and immediate-only real effects',()=>{
  const r=view.modelExperiments[0] as ExperimentReport;const html=renderToStaticMarkup(<ExperimentView report={r}/>);
  expect(html).toContain('Does held text alter this response?');expect(html).toContain('Between-condition response contrast');expect(html).toContain(r.id);expect(html).toContain('Step 64');
  expect(renderToStaticMarkup(<ExperimentView report={{...r,outcome:'noContrast'}}/>)).toContain('No distinguishing contrast');
  const probe=actions.state.recentReceipts.find(r=>r.request?.kind==='probeExperiment') as SustainedActionReceipt;
  expect(renderToStaticMarkup(<ExperimentReceiptView receipt={probe}/>)).toContain('only the immediate paired effect is observed');
  expect(renderToStaticMarkup(<SonarSetup config={config} setConfig={()=>{}}/>)).toContain('Allow customized experiments and named follow-ups');
 });
});
