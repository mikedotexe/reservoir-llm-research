import { record, finite, hash, vec, matrix, norm, origin, count, type SonarOrigin, type SonarCandidate, type SonarProbe } from './sonar';
export type SonarQuestion = 'state' | 'input' | 'recurrence';
export const sonarQuestion=(v:unknown):v is SonarQuestion=>v==='state'||v==='input'||v==='recurrence';
export const questionDescription=(q:SonarQuestion)=>({state:'Current starting state versus zero starting state',input:'Current held text input versus no held text input',recurrence:'Current recurrent gain versus recurrence turned off'}[q]);
export interface CompactValidation { seed:string; signedProbes:number; resolvedProbes:number; aggregateRelativeError:number|null; maximumRelativeError:number|null; absoluteErrorL2:number; responseL2:number; passed:boolean }
export interface SignedFallback { reason:string; positive:number[][]; negative:number[][] }
export interface CompactReport { version:'compact-scan-v2'; id:string; origin:SonarOrigin; epsilon:number; calibrationDirection:number[]; calibrationPositive:number[]; calibrationNegative:number[]; rowGains:number[]; minimumNormalizedDrive:number; validation:CompactValidation; fallback:SignedFallback|null; candidates:SonarCandidate[]; maximumLiveInputL2:number; maximumLiveStateL2:number }
export interface CompactView { report:CompactReport; immediateResponseMatrix:number[][] }
export interface QuestionReport { version:'compact-scan-v2'; id:string; question:SonarQuestion; origin:SonarOrigin; alternativeOrigin:SonarOrigin; epsilon:number; actualMapId:string; alternativeMapId:string; actualValidation:CompactValidation; alternativeValidation:CompactValidation; usedSignedFallback:boolean; unitInput:number[]|null; predictedGap:number[][]; measuredGap:number[][]; actualResponseL2:number[]; alternativeResponseL2:number[]; predictionRelativeError:number|null; linearPredictionValid:boolean; randomMedianGapL2:number; gainOverRandom:number|null }
export interface QuestionForecast { question:SonarQuestion; alternativeOrigin:SonarOrigin; actualDelta:number[]; alternativeDelta:number[]; differenceL2:number }
const optionalError=(v:unknown)=>v===null||finite(v,0);
export function validCompactValidation(v:unknown):v is CompactValidation {
  if(!record(v)||v.seed!=='20261118'||v.signedProbes!==32||!count(v.resolvedProbes,32)||!optionalError(v.aggregateRelativeError)||!optionalError(v.maximumRelativeError)||v.maximumRelativeError===null||!finite(v.absoluteErrorL2,0)||!finite(v.responseL2,0)||typeof v.passed!=='boolean')return false;
  const aggregate=v.aggregateRelativeError as number|null,max=v.maximumRelativeError as number;
  return (aggregate!==null)===(v.responseL2>1e-9)&&(aggregate===null||Math.abs(aggregate-v.absoluteErrorL2/v.responseL2)<1e-10)&&v.passed===(v.resolvedProbes>0&&aggregate!==null&&aggregate<=.01&&max<=.01);
}
export function validCompactReport(v:unknown):v is CompactReport {
  if(!record(v)||v.version!=='compact-scan-v2'||!hash(v.id)||!origin(v.origin)||v.epsilon!==.001||!vec(v.calibrationDirection,48,-1,1)||Math.abs(norm(v.calibrationDirection)-1)>1e-10||!vec(v.calibrationPositive,v.origin.state.length,-2,2)||!vec(v.calibrationNegative,v.origin.state.length,-2,2)||!vec(v.rowGains,v.origin.state.length,0,v.origin.controls.leak)||!finite(v.minimumNormalizedDrive,0,1)||!validCompactValidation(v.validation)||!finite(v.maximumLiveInputL2,Number.MIN_VALUE,.01)||v.maximumLiveStateL2!==.05)return false;
  if((v.fallback!==null)!==(!v.validation.passed||v.minimumNormalizedDrive<=1e-9))return false;
  if(v.fallback!==null&&(!record(v.fallback)||typeof v.fallback.reason!=='string'||!v.fallback.reason||!matrix(v.fallback.positive,48,v.origin.state.length,-2,2)||!matrix(v.fallback.negative,48,v.origin.state.length,-2,2)))return false;
  return Array.isArray(v.candidates)&&v.candidates.length<=2&&new Set(v.candidates.map(c=>c.direction)).size===v.candidates.length&&v.candidates.every(c=>record(c)&&(c.direction==='strongest'||c.direction==='weakest')&&vec(c.unitInput,48,-1,1)&&Math.abs(norm(c.unitInput)-1)<1e-10&&vec(c.positiveResponseL2,64,0,24)&&vec(c.negativeResponseL2,64,0,24)&&(c.positiveReturnStep===null||count(c.positiveReturnStep,60))&&(c.negativeReturnStep===null||count(c.negativeReturnStep,60)));
}
export function validCompactView(v:unknown):v is CompactView {return record(v)&&validCompactReport(v.report)&&matrix(v.immediateResponseMatrix,v.report.origin.state.length,48,-100,100);}
function sameAlternative(a:SonarOrigin,b:SonarOrigin,q:SonarQuestion):boolean {
  const expected={...a,state:q==='state'?Array(a.state.length).fill(0):a.state,heldVector:q==='input'?Array(48).fill(0):a.heldVector,controls:q==='recurrence'?{...a.controls,recurrentGain:0}:a.controls};
  return (Object.keys(expected) as (keyof SonarOrigin)[]).every(k=>JSON.stringify(expected[k])===JSON.stringify(b[k]));
}
export function validQuestionReport(v:unknown):v is QuestionReport {
  if(!record(v)||v.version!=='compact-scan-v2'||!hash(v.id)||!sonarQuestion(v.question)||!origin(v.origin)||!origin(v.alternativeOrigin)||!sameAlternative(v.origin,v.alternativeOrigin,v.question)||v.epsilon!==.001||!hash(v.actualMapId)||!hash(v.alternativeMapId)||!validCompactValidation(v.actualValidation)||!validCompactValidation(v.alternativeValidation)||typeof v.usedSignedFallback!=='boolean'||!(v.unitInput===null||vec(v.unitInput,48,-1,1)&&Math.abs(norm(v.unitInput)-1)<1e-10)||!Array.isArray(v.measuredGap)||![0,2].includes(v.measuredGap.length))return false;
  const n=v.measuredGap.length;
  if(!matrix(v.measuredGap,n,v.origin.state.length,-4,4)||!matrix(v.predictedGap,n,v.origin.state.length,-100,100)||!vec(v.actualResponseL2,n,0,24)||!vec(v.alternativeResponseL2,n,0,24)||!optionalError(v.predictionRelativeError)||typeof v.linearPredictionValid!=='boolean'||!finite(v.randomMedianGapL2,0,48)||!optionalError(v.gainOverRandom))return false;
  const measured=v.measuredGap,predicted=v.predictedGap;
  const magnitude=Math.hypot(...measured.flat()),error=Math.hypot(...measured.flatMap((row,i)=>row.map((x,j)=>x-predicted[i][j])));
  const relative=magnitude>1e-9?error/magnitude:null;
  const ratio=v.predictionRelativeError as number|null;
  const gain=v.unitInput!==null&&v.randomMedianGapL2>1e-9?measured.reduce((n,row)=>n+norm(row),0)/2/v.randomMedianGapL2:null;
  return (v.unitInput!==null)===measured.some(row=>norm(row)>1e-9)&&(ratio===null?relative===null:relative!==null&&Math.abs(ratio-relative)<1e-10)&&v.linearPredictionValid===(v.unitInput!==null&&!v.usedSignedFallback&&relative!==null&&relative<=.01)&&(v.actualValidation.passed&&v.alternativeValidation.passed||v.usedSignedFallback)&&(gain===null?v.gainOverRandom===null:typeof v.gainOverRandom==='number'&&Math.abs(gain-v.gainOverRandom)<1e-9);
}
export function validQuestionForecast(p:SonarProbe):boolean {
  const q=p.questionForecast;
  if(q===undefined)return p.direction!=='question'||p.rejection!==null;
  return p.direction==='question'&&p.rejection===null&&origin(p.forecastOrigin)&&vec(p.forecastResponseL2,64,0,24)&&record(q)&&sonarQuestion(q.question)&&origin(q.alternativeOrigin)&&sameAlternative(p.forecastOrigin,q.alternativeOrigin,q.question)&&vec(q.actualDelta,p.forecastOrigin.state.length,-2,2)&&vec(q.alternativeDelta,p.forecastOrigin.state.length,-2,2)&&finite(q.differenceL2,0,48)&&Math.abs(norm(q.actualDelta)-p.forecastResponseL2[0])<1e-10&&Math.abs(Math.hypot(...q.actualDelta.map((x,i)=>x-q.alternativeDelta[i]))-q.differenceL2)<1e-10;
}
