import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { validCompactView, validQuestionReport, validCompactValidation, type CompactView, type QuestionReport } from './compactSonar';
import { CompactScanView, QuestionView } from './MyReservoirSonar';
import { withSonar, validSonarView, type SonarOrigin } from './sonar';
import { DEFAULT_SUSTAINED_CONFIG, type SustainedActionReceipt } from './myReservoirTypes';
import { withAuthoredActionMode, validActionReceipt } from './authoredActions';

const unit=[1,...Array(47).fill(0)];
const vector=(value:number)=>[value,...Array(31).fill(0)];
const controls={leak:.65,recurrentGain:1,feedbackScale:.4};
const origin:SonarOrigin={step:19,seed:'20260909',rngState:'1234',modelSha256:'a'.repeat(64),historySha256:'b'.repeat(64),state:Array(32).fill(.2),heldVector:Array(48).fill(0),heldJournalId:null,controls,noiseAmplitude:.02,dt:1/3};
const validation={seed:'20261118',signedProbes:32,resolvedProbes:32,aggregateRelativeError:.001,maximumRelativeError:.002,absoluteErrorL2:.0001,responseL2:.1,passed:true};
const view:CompactView={report:{version:'compact-scan-v2',id:'c'.repeat(64),origin,epsilon:.001,calibrationDirection:unit,calibrationPositive:vector(.001),calibrationNegative:vector(-.001),rowGains:Array(32).fill(.4),minimumNormalizedDrive:.01,validation,fallback:null,candidates:[],maximumLiveInputL2:.004,maximumLiveStateL2:.05},immediateResponseMatrix:Array.from({length:32},()=>Array(48).fill(.4))};
const question:QuestionReport={version:'compact-scan-v2',id:'d'.repeat(64),question:'state',origin,alternativeOrigin:{...origin,state:Array(32).fill(0)},epsilon:.001,actualMapId:'c'.repeat(64),alternativeMapId:'e'.repeat(64),actualValidation:validation,alternativeValidation:validation,usedSignedFallback:false,unitInput:unit,predictedGap:[vector(.001),vector(-.001)],measuredGap:[vector(.001),vector(-.001)],actualResponseL2:[.002,.002],alternativeResponseL2:[.001,.001],predictionRelativeError:0,linearPredictionValid:true,randomMedianGapL2:.0005,gainOverRandom:2};
const config=withSonar(withAuthoredActionMode(DEFAULT_SUSTAINED_CONFIG,'authored-v3'),true);

describe('compact scanning and question evidence',()=>{
  it('enables v2 without enabling real probes',()=>{
    expect(config.sonar).toEqual({version:'compact-scan-v2',allowLiveProbe:false});
  });
  it('distinguishes validated coefficients from unvalidated signed fallback',()=>{
    expect(validCompactView(view)).toBe(true);
    expect(validCompactValidation({...validation,maximumRelativeError:.2})).toBe(false);
    const failed={...validation,maximumRelativeError:.2,passed:false};
    const fallback={...view,report:{...view.report,validation:failed,fallback:{reason:'Fresh-probe prediction error exceeded 1%',positive:Array.from({length:48},()=>vector(.001)),negative:Array.from({length:48},()=>vector(-.001))}}};
    expect(validCompactView(fallback)).toBe(true);
    expect(validCompactView({...fallback,report:{...fallback.report,fallback:null}})).toBe(false);
    const html=renderToStaticMarkup(<CompactScanView view={fallback} label="Test fallback"/>);
    expect(html).toContain('Signed measurement fallback');expect(html).toContain('not a validated linear predictor');
    expect(renderToStaticMarkup(<CompactScanView view={view} label="Test scan"/>)).toContain('Validated compact map');
  });
  it('binds counterfactual conditions and measured versus predicted evidence',()=>{
    expect(validQuestionReport(question)).toBe(true);
    expect(validQuestionReport({...question,alternativeOrigin:{...question.alternativeOrigin,rngState:'99'}})).toBe(false);
    expect(validQuestionReport({...question,predictionRelativeError:.8})).toBe(false);
    expect(validQuestionReport({...question,gainOverRandom:20})).toBe(false);
    const html=renderToStaticMarkup(<QuestionView report={question} label="Model-selected question"/>);
    expect(html).toContain('zero starting state');expect(html).toContain('Measured contrast L2');expect(html).toContain('copied numerical experiments');
    const unresolved={...question,unitInput:null,predictedGap:[],measuredGap:[],actualResponseL2:[],alternativeResponseL2:[],predictionRelativeError:null,linearPredictionValid:false,randomMedianGapL2:0,gainOverRandom:null};
    expect(validQuestionReport(unresolved)).toBe(true);
    expect(renderToStaticMarkup(<QuestionView report={unresolved} label="Unresolved"/>)).toContain('real question probe will be rejected');
  });
  it('requires source-bound operator views and rejects malformed compact arrays',()=>{
    const mirror={firstStep:19,lastStep:19,sampleCount:1,mean:Array(32).fill(.2),covarianceEigenvalues:Array(32).fill(0),principalAxes:[],explainedShares:[],projectedHistory:[[]],currentRms:.2,currentBoundaryCoordinates:0};
    const payload={sessionId:'one',generation:'2',checkpointSha256:'a'.repeat(64),step:19,state:origin.state,heldInput:origin.heldVector,mirror,modelScan:null,operatorScan:null,modelCompact:view,operatorCompact:null,modelQuestion:question,operatorQuestion:null};
    expect(validSonarView(payload,'one','2')).toBe(true);
    expect(validSonarView({...payload,operatorCompact:{...view,report:{...view.report,origin:{...origin,step:18}}}},'one','2')).toBe(false);
    expect(validCompactView({...view,immediateResponseMatrix:[[NaN]]})).toBe(false);
  });
  it('admits copied question receipts only under v2 and requires an actual receipt',()=>{
    const receipt:SustainedActionReceipt={journalId:'journal-example',attemptId:1,observedStep:18,appliedStep:19,status:'applied',request:{kind:'scanQuestion',question:'state'},rawTail:'NEXT: SCAN_QUESTION state',rejection:null,controlsBefore:controls,controlsAfter:controls,stateDeltaL2:0,stateDeltaMaxAbs:0,clippedCoordinates:0,sonarQuestion:{id:question.id,step:19}};
    expect(validActionReceipt(receipt,19)).toBe(true);
    expect(validActionReceipt({...receipt,sonarQuestion:undefined},19)).toBe(false);
    // Mode-specific checks precede optional input/diagnostic checks: old sessions cannot admit this action.
    expect(validActionReceipt(receipt,19,{...config,sonar:{version:'response-scan-v1',allowLiveProbe:true}})).toBe(false);
    expect(validActionReceipt({...receipt,stateDeltaL2:.001},19)).toBe(false);
  });
});
