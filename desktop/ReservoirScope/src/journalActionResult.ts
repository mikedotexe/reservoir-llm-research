import { invoke, isTauri } from '@tauri-apps/api/core';
import { validSonarView, type SonarView } from './sonar';
import type { SustainedActionReceipt, SustainedSummary } from './myReservoirTypes';

export type JournalSession = Pick<SustainedSummary, 'sessionId' | 'generation'>;
export function actionResultReference(receipt?: SustainedActionReceipt | null) {
  if (!receipt || receipt.status !== 'applied') return null;
  if (receipt.request?.kind === 'experiment' && receipt.experiment?.reportId) return { kind: 'experiment' as const, id: receipt.experiment.reportId, step: receipt.observedStep };
  if (receipt.request?.kind === 'scan' && receipt.sonarScan) return { kind: 'scan' as const, ...receipt.sonarScan };
  if (receipt.request?.kind === 'scanQuestion' && receipt.sonarQuestion) return { kind: 'question' as const, ...receipt.sonarQuestion };
  return null;
}
export function matchingActionResult(view: SonarView, reference: NonNullable<ReturnType<typeof actionResultReference>>) {
  if (reference.kind === 'experiment') {
    const report = view.modelExperiments?.find(value => value.id === reference.id && value.requestedStep === reference.step);
    return report ? { kind: 'experiment' as const, report } : null;
  }
  if (reference.kind === 'question') return view.modelQuestion?.id === reference.id && view.modelQuestion.origin.step === reference.step ? { kind: 'question' as const, report: view.modelQuestion } : null;
  if (view.modelCompact?.report.id === reference.id && view.modelCompact.report.origin.step === reference.step) return { kind: 'compact' as const, view: view.modelCompact };
  return view.modelScan?.id === reference.id && view.modelScan.origin.step === reference.step ? { kind: 'scan' as const, report: view.modelScan } : null;
}
export type MatchedActionResult = NonNullable<ReturnType<typeof matchingActionResult>>;
export async function loadJournalActionResult(session: JournalSession, reference: NonNullable<ReturnType<typeof actionResultReference>>) {
  if (!isTauri()) throw new Error('Open the native app to load saved measurements. The receipt remains available here.');
  // Passive read only: never run an operator scan or substitute the latest report.
  const view = await invoke<unknown>('observe_sustained_sonar', { ...session, scan: false, question: null });
  if (!validSonarView(view, session.sessionId, session.generation)) throw new Error('The saved measurements do not match this session.');
  return matchingActionResult(view, reference);
}
