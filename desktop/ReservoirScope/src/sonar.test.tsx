import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { DEFAULT_SUSTAINED_CONFIG, type SustainedActionReceipt } from './myReservoirTypes';
import { withAuthoredActionMode, withAuthoredActions, validAuthoredActionConfig, validActionReceipt } from './authoredActions';
import { withSonar, validMirror, validSonarView, type SonarMirror } from './sonar';
import { MirrorView, SonarSetup, SonarReceiptView } from './MyReservoirSonar';
const config={...withAuthoredActionMode(DEFAULT_SUSTAINED_CONFIG,'authored-v3'),sonar:{version:'response-scan-v1' as const,allowLiveProbe:true}};
const mirror:SonarMirror={firstStep:3,lastStep:3,sampleCount:1,mean:Array(32).fill(0),covarianceEigenvalues:Array(32).fill(0),principalAxes:[],explainedShares:[],projectedHistory:[[]],currentRms:0,currentBoundaryCoordinates:0};
const controls={leak:.65,recurrentGain:1,feedbackScale:.4};
const rejected:SustainedActionReceipt={journalId:'journal-example',attemptId:1,observedStep:3,appliedStep:4,status:'rejected',request:{kind:'probeScan',direction:'strongest',sign:'positive'},rawTail:'NEXT: PROBE_SCAN strongest positive',rejection:'No model-selected scan is available.',controlsBefore:controls,controlsAfter:controls,stateDeltaL2:0,stateDeltaMaxAbs:0,clippedCoordinates:0,sonarProbe:{direction:'strongest',sign:'positive',sourceScan:null,rejection:'No model-selected scan is available.',appliedVector:Array(48).fill(0),maximumStateL2:.05,forecastOrigin:null,forecastResponseL2:[]}};
describe('response scanner admission and meaning',()=>{
  it('keeps capability opt-in, immutable compatibility prerequisites and old modes',()=>{
    expect(withSonar(config,true).storageBudgetBytes).toBe(536870912);
    expect(withSonar(config,false).sonar).toBeUndefined();
    expect(DEFAULT_SUSTAINED_CONFIG.sonar).toBeUndefined();expect(validAuthoredActionConfig(config)).toBe(true);
    expect(validAuthoredActionConfig({...config,differenceGain:.1})).toBe(false);
    expect(validAuthoredActionConfig({...config,controlFeedback:undefined})).toBe(false);
    expect(withAuthoredActionMode(config,'authored-v2').sonar).toBeUndefined();
    expect(withAuthoredActions(config,false,undefined).sonar).toBeUndefined();
    const html=renderToStaticMarkup(<SonarSetup config={config} setConfig={()=>{}}/>);
    expect(html).toContain('Also allow real probes');expect(html).toContain('PULSE, TUNE and authored PROBE retain');
  });
  it('accepts a typed runtime rejection while refusing a claimed numerical effect',()=>{
    expect(validActionReceipt(rejected,4)).toBe(true);
    expect(validActionReceipt({...rejected,stateDeltaL2:.01},4)).toBe(false);
    expect(validActionReceipt({...rejected,status:'applied'},4)).toBe(false);
    expect(validActionReceipt({...rejected,sonarProbe:undefined},4)).toBe(false);
    expect(renderToStaticMarkup(<SonarReceiptView receipt={rejected}/>)).toContain('No probe applied');
  });
  it('requires source identity and honest passive history',()=>{
    expect(validMirror(mirror)).toBe(true);
    expect(validMirror({...mirror,sampleCount:128})).toBe(false);
    expect(validMirror({...mirror,principalAxes:[[1]]})).toBe(false);
    const view={sessionId:'one',generation:'2',checkpointSha256:'a'.repeat(64),step:3,state:Array(32).fill(0),heldInput:Array(48).fill(0),mirror,operatorScan:null,modelScan:null};
    expect(validSonarView(view,'one','2')).toBe(true);expect(validSonarView(view,'other','2')).toBe(false);
    expect(validSonarView({...view,step:4},'one','2')).toBe(false);
    expect(renderToStaticMarkup(<MirrorView mirror={mirror}/>)).toContain('single state does not define a trajectory');
  });
});
